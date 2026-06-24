type StatusProps = {
  complete: boolean
}

type UploadProps = {
  uploadFile: (
    e: React.ChangeEvent<HTMLInputElement>
  ) => void
}

export function HeroCard() {

  return (

    <div
      className="
        bg-white
        border
        border-[#E5E7EB]
        rounded-[16px]
        p-5
        shadow-sm
      "
    >

      <h1
        className="
          text-[28px]
          font-semibold
          text-[#111827]
          leading-tight
        "
      >
        📄 AI-Powered Contract Review Platform
      </h1>

      <p
        className="
          mt-2
          text-[#475467]
          text-[15px]
        "
      >
        Upload contracts to automatically
        extract clauses, validate compliance
        requirements, identify risks and
        generate mitigation recommendations.
      </p>

    </div>

  )

}

export function StatusCard({
  complete
}: StatusProps) {

  return (

    <div
      className="
        bg-white
        border
        border-[#E5E7EB]
        rounded-[14px]
        px-5
        py-4
        flex
        justify-between
        items-center
        shadow-sm
      "
    >

      <div
        className="
          text-[15px]
          font-semibold
          text-[#111827]
        "
      >

        {
          complete
            ? "Compliance analysis completed"
            : "Analysis status will be shown here"
        }

      </div>

      {
        complete && (

          <div
            className="
              bg-[#DCFCE7]
              text-[#166534]
              px-3
              py-1.5
              rounded-full
              text-[13px]
              font-semibold
            "
          >
            ✓ Complete
          </div>

        )
      }

    </div>

  )

}

export function UploadCard({
  uploadFile
}: UploadProps) {

  return (

    <div
      className="
        bg-white
        border
        border-[#E5E7EB]
        rounded-[16px]
        shadow-sm
        overflow-hidden
      "
    >

      <div
        className="
          px-6
          py-5
          border-b
          border-[#E5E7EB]
          bg-white
        "
      >

        <div
          className="
            text-[18px]
            font-semibold
            text-[#111827]
          "
        >
          Upload Contract
        </div>

        <div
          className="
            mt-1
            text-[14px]
            text-[#6B7280]
          "
        >
          Upload PDF / DOC / DOCX for analysis
        </div>

      </div>

      <div className="p-6">

        <label
          className="
            flex
            flex-col
            items-center
            justify-center
            h-52
            rounded-[14px]
            border-2
            border-dashed
            border-[#CBD5E1]
            cursor-pointer
            transition-all
            duration-200
            hover:border-[#810055]
            hover:bg-[#FDF4FF]
          "
        >

          <div
            className="
              text-5xl
            "
          >
            📄
          </div>

          <div
            className="
              mt-4
              text-[17px]
              font-semibold
              text-[#111827]
            "
          >
            Click to Upload
          </div>

          <div
            className="
              mt-1
              text-[14px]
              text-[#6B7280]
            "
          >
            PDF / DOCX / DOC
          </div>

          <input
            type="file"
            accept=".pdf,.doc,.docx"
            className="hidden"
            onChange={uploadFile}
          />

        </label>

      </div>

    </div>

  )

}