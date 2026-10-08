const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

function loadResumeCenterApi(fetch, env = {}) {
  let token = 'test-candidate-token';
  const exports = {};
  const source = fs.readFileSync(path.join(__dirname, '../services/resumeCenterApi.ts'), 'utf8');
  const js = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;

  const mockDocument = {
    cookie: 'csrf_token=test-csrf-token-12345;',
  };

  const context = {
    exports,
    process: { env: { NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1', ...env } },
    fetch,
    document: mockDocument,
    window: { location: { hostname: 'localhost' } },
    localStorage: { getItem: () => token },
    Response,
    URL,
    URLSearchParams,
    Headers,
    FormData,
    Blob,
  };

  vm.runInNewContext(js, context);
  return { api: exports.resumeCenterApi, setToken: (v) => { token = v; } };
}

test('resumeCenterApi includes auth token and csrf header in requests', async () => {
  let capturedHeaders = null;
  const { api } = loadResumeCenterApi(async (url, init) => {
    capturedHeaders = init.headers;
    return Response.json([{ id: 1, title: 'Sample Resume' }]);
  });

  const resumes = await api.getResumes();
  assert.equal(resumes.length, 1);
  assert.equal(capturedHeaders.Authorization, 'Bearer test-candidate-token');
  assert.equal(capturedHeaders['X-CSRF-Token'], 'test-csrf-token-12345');
});

test('resumeCenterApi.getResumes sends search and status query parameters correctly', async () => {
  let requestedUrl = null;
  const { api } = loadResumeCenterApi(async (url) => {
    requestedUrl = url;
    return Response.json([]);
  });

  await api.getResumes('software engineer', 'compiled');
  assert.ok(requestedUrl.includes('search=software+engineer') || requestedUrl.includes('search=software%20engineer'));
  assert.ok(requestedUrl.includes('status_filter=compiled'));
});

test('resumeCenterApi.createResume posts structured resume payload with JSON Content-Type', async () => {
  let postMethod = null;
  let postBody = null;
  let contentType = null;

  const { api } = loadResumeCenterApi(async (url, init) => {
    postMethod = init.method;
    postBody = JSON.parse(init.body);
    contentType = init.headers['Content-Type'];
    return Response.json({ id: 42, title: 'DevOps Resume', status: 'DRAFT' });
  });

  const result = await api.createResume({
    title: 'DevOps Resume',
    template_id: 2,
    structured_data: {
      personal_info: { full_name: 'Dev Candidate' },
      skills: ['Docker', 'Kubernetes'],
    },
  });

  assert.equal(result.id, 42);
  assert.equal(postMethod, 'POST');
  assert.equal(contentType, 'application/json');
  assert.equal(postBody.title, 'DevOps Resume');
  assert.equal(postBody.structured_data.skills[0], 'Docker');
});

test('resumeCenterApi.compileResume triggers compilation endpoint and returns status', async () => {
  let compiledEndpoint = null;
  const { api } = loadResumeCenterApi(async (url, init) => {
    compiledEndpoint = url;
    return Response.json({
      status: 'COMPILED',
      latex_available: true,
      message: 'Compiled successfully',
    });
  });

  const res = await api.compileResume(99);
  assert.ok(compiledEndpoint.endsWith('/resumes/99/compile'));
  assert.equal(res.status, 'COMPILED');
  assert.equal(res.latex_available, true);
});

test('resumeCenterApi.approveTailoring sends approved data non-destructively', async () => {
  let requestedUrl = null;
  let approvalBody = null;

  const { api } = loadResumeCenterApi(async (url, init) => {
    requestedUrl = url;
    approvalBody = JSON.parse(init.body);
    return Response.json({
      message: 'Approved',
      resume_id: 101,
      version_id: 201,
      title: 'Senior Tailored Resume',
    });
  });

  const approved = await api.approveTailoring(10, {
    approved_resume_data: { summary: 'Aligned with Cloud requirements' },
    create_new_resume: true,
    new_title: 'Senior Tailored Resume',
    change_summary: 'Tailored for Cloud Architect role',
  });

  assert.ok(requestedUrl.endsWith('/resume-tailoring/10/approve'));
  assert.equal(approved.resume_id, 101);
  assert.equal(approvalBody.create_new_resume, true);
  assert.equal(approvalBody.new_title, 'Senior Tailored Resume');
});
