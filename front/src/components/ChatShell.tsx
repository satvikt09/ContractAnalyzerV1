import React from "react";

type Props = {
  children: React.ReactNode;
};

export default function ChatShell({ children }: Props) {
  return (
    <div className="bg-[#F3F4F6] border border-[#E5E7EB] rounded-2xl p-5 space-y-4">
      {children}
    </div>
  );
}