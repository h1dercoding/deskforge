import React, { useState } from "react";

interface FormField {
  name: string;
  label: string;
  type: string; // text, number, date, select, checkbox, email, url
  required?: boolean;
  options?: string[];
  placeholder?: string;
}

interface FormProps {
  spec: {
    props: {
      title?: string;
      fields?: FormField[];
      submitLabel?: string;
    };
  };
  dataSourceRef?: string;
  actions?: any[];
}

export function Form({ spec, dataSourceRef, actions }: FormProps) {
  const fields = spec.props.fields || [];
  const [values, setValues] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (name: string, value: any) => {
    setValues((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => { const e = { ...prev }; delete e[name]; return e; });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};
    fields.forEach((f) => {
      if (f.required && !values[f.name]) {
        newErrors[f.name] = `${f.label} is required`;
      }
      if (f.type === "email" && values[f.name] && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values[f.name])) {
        newErrors[f.name] = "Invalid email format";
      }
    });
    setErrors(newErrors);
    if (Object.keys(newErrors).length === 0) {
      // Send create action to parent
      const createAction = actions?.find((a) => a.type === "create");
      if (createAction) {
        window.parent.postMessage({
          type: "action",
          action: createAction,
          data: values,
        }, "*");
      }
      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 3000);
      setValues({});
    }
  };

  const renderField = (field: FormField) => {
    const baseClass = "w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

    switch (field.type) {
      case "select":
        return (
          <select className={baseClass} value={values[field.name] || ""} onChange={(e) => handleChange(field.name, e.target.value)}>
            <option value="">{field.placeholder || "Select..."}</option>
            {(field.options || []).map((opt) => <option key={opt} value={opt}>{opt}</option>)}
          </select>
        );
      case "checkbox":
        return (
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={values[field.name] || false} onChange={(e) => handleChange(field.name, e.target.checked)} className="h-4 w-4" />
            <span className="text-sm">{field.label}</span>
          </label>
        );
      case "date":
        return <input type="date" className={baseClass} value={values[field.name] || ""} onChange={(e) => handleChange(field.name, e.target.value)} />;
      case "number":
        return <input type="number" className={baseClass} value={values[field.name] || ""} onChange={(e) => handleChange(field.name, e.target.value)} placeholder={field.placeholder} />;
      default:
        return <input type={field.type || "text"} className={baseClass} value={values[field.name] || ""} onChange={(e) => handleChange(field.name, e.target.value)} placeholder={field.placeholder} />;
    }
  };

  return (
    <div className="border rounded-lg bg-white p-6">
      <h3 className="font-semibold text-gray-900 mb-4">{spec.props.title || "Form"}</h3>
      {submitted && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-green-700 text-sm">
          Submitted successfully!
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        {fields.map((field) => (
          <div key={field.name}>
            {field.type !== "checkbox" && (
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {field.label} {field.required && <span className="text-red-500">*</span>}
              </label>
            )}
            {renderField(field)}
            {errors[field.name] && <p className="text-red-500 text-xs mt-1">{errors[field.name]}</p>}
          </div>
        ))}
        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 transition-colors">
          {spec.props.submitLabel || "Submit"}
        </button>
      </form>
    </div>
  );
}
