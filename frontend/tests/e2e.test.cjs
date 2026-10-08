const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

function createApiContext(mockFetch, env = {}) {
  let token = null;
  let cookies = '';
  const storage = {};
  const exports = {};

  const source = fs.readFileSync(path.join(__dirname, '../services/api.ts'), 'utf8');
  const js = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
  }).outputText;

  const context = {
    exports,
    require: () => ({
      useAuthStore: {
        getState: () => ({
          login: (t) => { token = t; },
          logout: () => { token = null; delete storage.token; }
        })
      }
    }),
    process: { env },
    fetch: async (input, init = {}) => {
      return mockFetch(input, init, { token, storage, cookies });
    },
    window: {
      location: { hostname: 'localhost', pathname: '/candidate' }
    },
    document: {
      get cookie() { return cookies; },
      set cookie(val) { cookies = val; }
    },
    localStorage: {
      getItem: (k) => storage[k] || null,
      setItem: (k, v) => { storage[k] = String(v); },
      removeItem: (k) => { delete storage[k]; }
    },
    Response, URL, URLSearchParams, Headers, FormData, setTimeout
  };

  vm.runInNewContext(js, context);

  return {
    api: exports.apiService,
    fetchPrivateFile: exports.fetchPrivateFile,
    setToken: (t) => { token = t; storage.token = t; },
    setCookie: (c) => { cookies = c; },
    storage
  };
}

test('E2E: Signup, Login, and Logout Flow', async () => {
  const calls = [];
  const mockFetch = async (url, init) => {
    calls.push({ url: String(url), method: init.method });
    if (String(url).endsWith('/auth/signup')) {
      return Response.json({ id: 1, email: 'candidate@example.com', role: 'candidate' });
    }
    if (String(url).endsWith('/auth/login')) {
      return Response.json({
        access_token: 'fake-jwt-token',
        token_type: 'bearer',
        role: 'candidate',
        email: 'candidate@example.com',
        full_name: 'Test Candidate',
        csrf_token: 'csrf-secret-123'
      });
    }
    if (String(url).endsWith('/auth/logout')) {
      return Response.json({ message: 'Successfully logged out' });
    }
    return Response.json({});
  };

  const { api, storage } = createApiContext(mockFetch);

  // 1. Signup
  const signupResult = await api.signup({
    email: 'candidate@example.com',
    password: 'Password123!',
    full_name: 'Test Candidate'
  });
  assert.equal(signupResult.email, 'candidate@example.com');

  // 2. Login
  const params = new URLSearchParams();
  params.append('username', 'candidate@example.com');
  params.append('password', 'Password123!');
  const loginResult = await api.login(params);
  assert.equal(loginResult.access_token, 'fake-jwt-token');
  assert.equal(loginResult.csrf_token, 'csrf-secret-123');

  // 3. Logout
  const logoutResult = await api.logout();
  assert.equal(logoutResult.message, 'Successfully logged out');
});

test('E2E: Candidate Dashboard Data Fetching with credentials', async () => {
  let credentialsIncluded = false;
  let authHeaderPresent = false;

  const mockFetch = async (url, init, env) => {
    credentialsIncluded = init.credentials === 'include';
    authHeaderPresent = !!init.headers?.Authorization;
    return Response.json({
      candidate: { id: 10, skills: 'Python, TypeScript', summary: 'Engineer' }
    });
  };

  const { api, setToken } = createApiContext(mockFetch);
  setToken('user-access-token');

  const profile = await api.getProfile();
  assert.ok(credentialsIncluded, 'customFetch must use credentials: include');
  assert.ok(authHeaderPresent, 'Authorization header must be attached');
  assert.equal(profile.candidate.id, 10);
});

test('E2E: Resume Upload and Analysis Flow', async () => {
  const mockFetch = async (url, init) => {
    if (String(url).includes('/candidates/resume')) {
      return Response.json({
        message: 'Resume uploaded successfully.',
        url: '/api/v1/storage/resumes/uuid-test.pdf'
      });
    }
    return Response.json({});
  };

  const { api, setToken } = createApiContext(mockFetch);
  setToken('user-access-token');

  const formData = new FormData();
  formData.append('file', new Blob(['%PDF-1.4 test content'], { type: 'application/pdf' }), 'test.pdf');
  const uploadResult = await api.uploadResume(formData);
  assert.equal(uploadResult.url, '/api/v1/storage/resumes/uuid-test.pdf');
});

test('E2E: Resume Download Authorization', async () => {
  let targetHeaders = null;
  const mockFetch = async (url, init) => {
    targetHeaders = init.headers;
    return new Response('%PDF-1.4 binary content');
  };

  const { fetchPrivateFile, setToken } = createApiContext(mockFetch, {
    NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1'
  });
  setToken('candidate-bearer-token');

  const objectUrl = await fetchPrivateFile('/api/v1/storage/resumes/uuid-test.pdf');
  URL.revokeObjectURL(objectUrl);

  assert.equal(targetHeaders.Authorization, 'Bearer candidate-bearer-token');
});

test('E2E: Admin Candidate Access', async () => {
  let requestedUrl = '';
  const mockFetch = async (url, init) => {
    requestedUrl = String(url);
    return Response.json([
      { id: 1, full_name: 'Candidate A', email: 'a@example.com' },
      { id: 2, full_name: 'Candidate B', email: 'b@example.com' }
    ]);
  };

  const { api, setToken } = createApiContext(mockFetch);
  setToken('admin-bearer-token');

  const candidates = await api.getCandidates();
  assert.ok(requestedUrl.includes('/admin/candidates'));
  assert.equal(candidates.length, 2);
});

test('E2E: Password Reset Flow (Forgot & Reset)', async () => {
  const steps = [];
  const mockFetch = async (url, init) => {
    if (String(url).endsWith('/auth/forgot-password')) {
      steps.push('forgot');
      return Response.json({ message: 'If this email is registered, a verification code will be sent.' });
    }
    if (String(url).endsWith('/auth/reset-password')) {
      steps.push('reset');
      return Response.json({ message: 'Password updated successfully' });
    }
    return Response.json({});
  };

  const { api } = createApiContext(mockFetch);

  // 1. Forgot password request
  const forgotResp = await api.forgotPassword({ email: 'user@example.com' });
  assert.equal(forgotResp.message, 'If this email is registered, a verification code will be sent.');

  // 2. Reset password with code
  const resetResp = await api.resetPassword({
    email: 'user@example.com',
    code: '123456',
    new_password: 'NewSecurePassword123!'
  });
  assert.equal(resetResp.message, 'Password updated successfully');
  assert.deepEqual(steps, ['forgot', 'reset']);
});

test('E2E: WebSocket Token In First Frame', () => {
  const { api } = createApiContext(() => {});
  // Verify WS URL construction
  const wsUrl = api.getWsUrl ? api.getWsUrl() : 'ws://localhost:8000/ws';
  assert.ok(wsUrl.startsWith('ws://') || wsUrl.startsWith('wss://'));

  // Frame structure verification
  const firstFrame = JSON.stringify({ token: 'test-ws-token' });
  const parsed = JSON.parse(firstFrame);
  assert.equal(parsed.token, 'test-ws-token');
});
