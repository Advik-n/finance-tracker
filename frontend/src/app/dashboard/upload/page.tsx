"use client";

import { useState } from "react";
import { Upload, FileText, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { useDropzone } from "react-dropzone";

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<Record<string, string>>({});

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "application/pdf": [".pdf"],
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
    },
    onDrop: (acceptedFiles) => {
      setFiles([...files, ...acceptedFiles]);
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleUpload = async () => {
    setUploading(true);
    
    for (const file of files) {
      setUploadStatus((prev) => ({ ...prev, [file.name]: "uploading" }));
      
      try {
        const formData = new FormData();
        formData.append("file", file);
        
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/upload/statement`,
          {
            method: "POST",
            body: formData,
            credentials: "include",
          }
        );
        
        if (!response.ok) throw new Error("Upload failed");
        
        setUploadStatus((prev) => ({ ...prev, [file.name]: "success" }));
      } catch (error) {
        setUploadStatus((prev) => ({ ...prev, [file.name]: "error" }));
      }
    }
    
    setUploading(false);
  };

  const removeFile = (fileName: string) => {
    setFiles(files.filter((f) => f.name !== fileName));
    const newStatus = { ...uploadStatus };
    delete newStatus[fileName];
    setUploadStatus(newStatus);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Upload Statements</h1>
        <p className="text-muted-foreground">
          Upload your bank statements to automatically import transactions
        </p>
      </div>

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-12 text-center transition-colors ${
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50"
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
        <h3 className="mt-4 text-lg font-semibold">
          {isDragActive ? "Drop files here" : "Drag & drop files here"}
        </h3>
        <p className="mt-2 text-sm text-muted-foreground">
          or click to browse. Supports PDF, CSV, and Excel files up to 10MB.
        </p>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="rounded-lg border bg-card">
          <div className="border-b p-4">
            <h3 className="font-semibold">Files to Upload</h3>
          </div>
          <ul className="divide-y">
            {files.map((file) => (
              <li
                key={file.name}
                className="flex items-center justify-between p-4"
              >
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {uploadStatus[file.name] === "uploading" && (
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  )}
                  {uploadStatus[file.name] === "success" && (
                    <CheckCircle className="h-5 w-5 text-income" />
                  )}
                  {uploadStatus[file.name] === "error" && (
                    <XCircle className="h-5 w-5 text-expense" />
                  )}
                  {!uploadStatus[file.name] && (
                    <button
                      onClick={() => removeFile(file.name)}
                      className="text-sm text-muted-foreground hover:text-foreground"
                    >
                      Remove
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
          <div className="border-t p-4">
            <button
              onClick={handleUpload}
              disabled={uploading || files.length === 0}
              className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload All
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-4 font-semibold">Supported Formats</h3>
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <h4 className="font-medium">PDF Statements</h4>
            <p className="text-sm text-muted-foreground">
              Most bank PDF statements are supported. Our AI extracts transactions automatically.
            </p>
          </div>
          <div>
            <h4 className="font-medium">CSV Files</h4>
            <p className="text-sm text-muted-foreground">
              Export transactions from your bank as CSV for quick import.
            </p>
          </div>
          <div>
            <h4 className="font-medium">Excel Files</h4>
            <p className="text-sm text-muted-foreground">
              Upload .xlsx or .xls files with transaction data.
            </p>
          </div>
        </div>
      </div>

      {/* Manual Transaction Entry */}
      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-4 font-semibold">Quick Add Transaction</h3>
        <ManualTransactionForm />
      </div>
    </div>
  );
}

function ManualTransactionForm() {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [form, setForm] = useState({
    amount: "",
    description: "",
    category: "",
    type: "DEBIT",
    date: new Date().toISOString().split("T")[0],
  });

  const categories = [
    "Petrol",
    "Groceries/Ration",
    "Fast Food",
    "Restaurants",
    "Utilities",
    "Shopping",
    "Entertainment",
    "Healthcare",
    "Transport",
    "Education",
    "Other",
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/transactions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            amount: parseFloat(form.amount),
            description: form.description,
            merchant_name: form.description,
            transaction_type: form.type,
            transaction_date: form.date,
          }),
        }
      );
      
      if (response.ok) {
        setSuccess(true);
        setForm({
          amount: "",
          description: "",
          category: "",
          type: "DEBIT",
          date: new Date().toISOString().split("T")[0],
        });
        setTimeout(() => setSuccess(false), 3000);
      }
    } catch (error) {
      console.error("Failed to add transaction:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {success && (
        <div className="rounded-md bg-income/10 p-3 text-sm text-income">
          Transaction added successfully!
        </div>
      )}
      
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium">Amount (₹)</label>
          <input
            type="number"
            step="0.01"
            required
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            placeholder="500.00"
            value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
          />
        </div>
        
        <div className="space-y-2">
          <label className="text-sm font-medium">Type</label>
          <select
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            value={form.type}
            onChange={(e) => setForm({ ...form, type: e.target.value })}
          >
            <option value="DEBIT">Expense</option>
            <option value="CREDIT">Income</option>
          </select>
        </div>
        
        <div className="space-y-2">
          <label className="text-sm font-medium">Description</label>
          <input
            type="text"
            required
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            placeholder="e.g., Petrol at Indian Oil"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </div>
        
        <div className="space-y-2">
          <label className="text-sm font-medium">Category</label>
          <select
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          >
            <option value="">Auto-detect</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
        
        <div className="space-y-2">
          <label className="text-sm font-medium">Date</label>
          <input
            type="date"
            required
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            value={form.date}
            onChange={(e) => setForm({ ...form, date: e.target.value })}
          />
        </div>
      </div>
      
      <button
        type="submit"
        disabled={loading}
        className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 disabled:opacity-50"
      >
        {loading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <CheckCircle className="mr-2 h-4 w-4" />
        )}
        Add Transaction
      </button>
    </form>
  );
}
