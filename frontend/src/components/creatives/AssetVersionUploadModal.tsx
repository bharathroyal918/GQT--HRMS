import React, { useState } from "react";
import { X, UploadCloud, FileText, AlertCircle } from "lucide-react";
import { Button } from "../ui/Button";

interface AssetVersionUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (formData: FormData) => Promise<void>;
  requestCode: string;
  nextVersionNumber: number;
}

export const AssetVersionUploadModal: React.FC<AssetVersionUploadModalProps> = ({
  isOpen,
  onClose,
  onUpload,
  requestCode,
  nextVersionNumber,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [designerNotes, setDesignerNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      const validTypes = ["image/png", "image/jpeg", "image/webp", "application/pdf"];
      if (!validTypes.includes(selected.type)) {
        setError("Only PNG, JPG, WebP images and PDF documents are permitted.");
        setFile(null);
        return;
      }
      if (selected.size > 15 * 1024 * 1024) {
        setError("File size cannot exceed 15MB limit.");
        setFile(null);
        return;
      }
      setError(null);
      setFile(selected);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select an asset file to upload.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      const fd = new FormData();
      fd.append("file", file);
      if (designerNotes.trim()) {
        fd.append("designer_notes", designerNotes.trim());
      }
      await onUpload(fd);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.file?.[0] || err?.response?.data?.detail || "Upload failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden animate-scale-up">
        <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50">
          <div>
            <h3 className="font-semibold text-slate-900 text-base">
              Upload Design Deliverable (v{nextVersionNumber})
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">Requisition: {requestCode}</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          {/* Dropzone container */}
          <div className="border-2 border-dashed border-slate-200 hover:border-indigo-400 rounded-xl p-6 text-center transition-colors">
            <input
              type="file"
              id="file-upload"
              accept=".png,.jpg,.jpeg,.webp,.pdf"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              <UploadCloud className="w-8 h-8 text-indigo-500 mx-auto mb-2" />
              <span className="text-xs font-semibold text-indigo-600 hover:underline">
                Click to browse file
              </span>
              <span className="text-xs text-slate-400 block mt-1">
                Supported formats: PNG, JPG, WebP, PDF (Max 15MB)
              </span>
            </label>

            {file && (
              <div className="mt-4 p-3 bg-indigo-50/60 rounded-lg flex items-center justify-between border border-indigo-100 text-xs text-slate-800 text-left">
                <div className="flex items-center gap-2 overflow-hidden">
                  <FileText className="w-4 h-4 text-indigo-600 shrink-0" />
                  <span className="font-medium truncate">{file.name}</span>
                </div>
                <span className="text-slate-500 text-[11px] shrink-0 font-mono">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </span>
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Designer Version Notes / Iteration Summary
            </label>
            <textarea
              rows={3}
              value={designerNotes}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setDesignerNotes(e.target.value)}
              placeholder="Detail changes made in this revision (e.g. typography adjusted, high-res logo replaced, deadline updated)..."
              className="w-full text-xs rounded-lg border border-slate-300 p-2.5 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
            <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSubmitting} disabled={!file}>
              Upload & Submit for Review
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

