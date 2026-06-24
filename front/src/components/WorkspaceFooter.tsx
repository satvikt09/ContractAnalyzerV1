type Props = {
    uploadFile:
    (
        e: React.ChangeEvent<
            HTMLInputElement
        >
    ) => void

    uploadedFile: string
}

export default function WorkspaceFooter({
    uploadFile,
    uploadedFile
}: Props) {

    return (

        <div
            className="
        border-t
        border-[#E5E7EB]
        bg-white
      "
        >

            <div
                className="
          px-5
          pt-3
          pb-2
        "
            >

                {
                    uploadedFile
                        ? (

                            <div
                                className="
                inline-flex
                items-center
                gap-2
                bg-[#EEF2FF]
                border
                border-[#C7D2FE]
                rounded-full
                px-3
                py-1.5
                text-[#1D4ED8]
                text-sm
              "
                            >
                                📄 {uploadedFile}
                            </div>

                        )
                        : (

                            <div
                                className="
                text-sm
                text-[#6B7280]
              "
                            >
                                Drag & drop files here or use + button
                            </div>

                        )
                }

            </div>

            <div
                className="
          flex
          items-center
          gap-3
          p-4
          border-t
          border-[#E5E7EB]
        "
            >

                <label
                    className="
            flex
            items-center
            justify-center
            w-11
            h-11
            rounded-xl
            border
            border-[#CBD5E1]
            cursor-pointer
            hover:bg-[#F3F4F6]
          "
                >
                    +

                    <input
                        type="file"
                        className="hidden"
                        accept=".pdf,.doc,.docx"
                        onChange={uploadFile}
                    />
                </label>

                <input
                    placeholder="
          Ask for bullet-point summaries or clarifications…
          "
                    className="
            flex-1
            border
            border-[#CBD5E1]
            rounded-xl
            px-4
            py-3
          "
                />

                <button
                    className="
            w-12
            h-12
            rounded-xl
            bg-[#111827]
            text-white
          "
                >
                    →
                </button>

            </div>

        </div>

    )

}