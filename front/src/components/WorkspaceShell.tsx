type Props = {
    children: React.ReactNode
}

export default function WorkspaceShell(
    { children }: Props
) {

    return (

        <div
            className="
        bg-white
        border
        border-[#E5E7EB]
        rounded-[16px]
        overflow-hidden
        shadow-sm
      "
        >

            {children}

        </div>

    )

}