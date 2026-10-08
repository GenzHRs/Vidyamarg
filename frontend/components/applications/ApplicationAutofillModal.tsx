"use client";

import { useEffect, useState } from "react";
import { 
  Sparkles, ShieldAlert, CheckCircle2, Lock, ArrowRight, 
  RefreshCw, FileText, Check, AlertCircle, ExternalLink 
} from "lucide-react";
import { autofillApi, AutofillMapResponse } from "@/services/autofillApi";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";

interface ApplicationAutofillModalProps {
  isOpen: boolean;
  onClose: () => void;
  jobTitle?: string;
  company?: string;
  applicationUrl?: string;
}

export function ApplicationAutofillModal({
  isOpen,
  onClose,
  jobTitle = "Software Position",
  company = "Target Employer",
  applicationUrl
}: ApplicationAutofillModalProps) {
  const [loading, setLoading] = useState(false);
  const [autofillData, setAutofillData] = useState<AutofillMapResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const loadFormMap = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await autofillApi.mapForm(applicationUrl);
      setAutofillData(data);
    } catch (err: any) {
      setErrorMsg(err.message || "AI Application Autofill requires a Plus or Pro subscription.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      setIsSubmitted(false);
      loadFormMap();
    }
  }, [isOpen]);

  const handleConfirmSubmit = () => {
    setIsSubmitted(true);
    setTimeout(() => {
      onClose();
    }, 2000);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="AI Application Form Autofill" className="max-w-2xl">
      <div className="space-y-6 font-sans p-1">
        {/* Header Summary */}
        <div className="flex items-center justify-between pb-4 border-b border-app-border">
          <div>
            <h3 className="text-base font-bold text-app-text">{jobTitle}</h3>
            <p className="text-xs text-app-text-muted">{company}</p>
          </div>
          <Badge variant="outline" className="text-xs px-2.5 py-1">
            <Sparkles size={13} className="mr-1 inline text-blue-500" />
            AI Application Agent
          </Badge>
        </div>

        {errorMsg && (
          <Alert variant="error" className="text-xs">
            {errorMsg}
          </Alert>
        )}

        {loading ? (
          <div className="p-10 text-center space-y-3 bg-app-surface/50 rounded-2xl border border-app-border">
            <RefreshCw size={24} className="animate-spin mx-auto text-blue-600" />
            <p className="text-xs font-semibold text-app-text-muted">
              Retrieving canonical profile from PostgreSQL & mapping application fields...
            </p>
          </div>
        ) : autofillData?.upgrade_required || errorMsg?.includes("Plus and Pro") ? (
          /* FREE USER UPGRADE BANNER */
          <Card className="p-6 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white border border-indigo-500/30 rounded-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30 shrink-0">
                <Lock size={20} />
              </div>
              <div>
                <h4 className="text-base font-bold text-white">Plus & Pro Subscription Feature</h4>
                <p className="text-xs text-blue-200/80 mt-0.5">
                  AI Application Autofill automatically fills external job application forms.
                </p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-2 text-blue-100">
              <p className="font-semibold text-amber-300">
                "AI Application Autofill is available on Plus and Pro. Upgrade to use automatic form filling."
              </p>
              <ul className="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
                <li>Free users: Upload, extract, candidate data storage, job search, manual apply</li>
                <li>Plus & Pro: Automated external website form mapping, semantic question answers, zero-hallucination validation</li>
              </ul>
            </div>

            <div className="pt-2 flex justify-end gap-3">
              <Button variant="outline" size="sm" onClick={onClose} className="text-xs bg-white/10 border-white/20 text-white hover:bg-white/20">
                Close
              </Button>
              <Button size="sm" className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs">
                Upgrade to Plus / Pro
                <ArrowRight size={14} className="ml-1.5" />
              </Button>
            </div>
          </Card>
        ) : autofillData?.can_autofill ? (
          /* PLUS / PRO AUTOFILLED FORM REVIEW */
          <div className="space-y-5">
            <div className="p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="text-xs font-bold text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
                  <CheckCircle2 size={14} /> Canonical PostgreSQL Candidate Data
                </span>
                <p className="text-[11px] text-app-text-muted">
                  Active Resume: <strong>{autofillData.active_resume_title || "Primary Resume"}</strong>
                </p>
              </div>
              <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px]">
                {autofillData.user_subscription?.toUpperCase() || "PLUS"} ENTITLED
              </Badge>
            </div>

            {isSubmitted ? (
              <div className="p-8 text-center space-y-2 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl">
                <CheckCircle2 size={36} className="mx-auto text-emerald-500" />
                <h4 className="text-base font-bold text-emerald-700 dark:text-emerald-400">
                  Application Prepared & Verified!
                </h4>
                <p className="text-xs text-app-text-muted">
                  Proceeding to final submission review...
                </p>
              </div>
            ) : (
              <>
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-app-text-muted">
                    Auto-Mapped Application Fields
                  </h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {Object.entries(autofillData.mapped_fields || {}).map(([key, field]) => (
                      <div key={key} className="p-3 rounded-xl border border-app-border bg-app-surface flex items-center justify-between text-xs">
                        <div>
                          <span className="font-semibold text-app-text block">{field.label}</span>
                          <span className={field.is_available ? "text-app-text-muted" : "text-amber-600 dark:text-amber-400 font-medium"}>
                            {field.value}
                          </span>
                        </div>
                        {field.is_available ? (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 font-bold border border-emerald-500/20">
                            Available
                          </span>
                        ) : (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-600 font-bold border border-amber-500/20">
                            Missing
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-app-surface border border-app-border text-xs text-app-text-muted flex items-center justify-between">
                  <span>{autofillData.review_prompt || "Application form is ready. Review and submit?"}</span>
                </div>

                <div className="pt-2 flex justify-end gap-3">
                  <Button variant="outline" size="sm" onClick={onClose} className="text-xs">
                    Cancel
                  </Button>
                  <Button size="sm" onClick={handleConfirmSubmit} className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs">
                    <Check size={14} className="mr-1.5" />
                    Submit Application
                  </Button>
                </div>
              </>
            )}
          </div>
        ) : null}
      </div>
    </Modal>
  );
}
