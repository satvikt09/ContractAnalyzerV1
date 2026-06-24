type Props = {
  rows: any[]
}

export default function RiskTable({
  rows
}: Props) {

  return (

    <div
      className="
        bg-white
        rounded-2xl
        shadow
        p-6
        mt-6
        overflow-auto
      "
    >

      <h2
        className="
          text-2xl
          font-semibold
          mb-4
        "
      >
        Risk Assessment Results
      </h2>

      <table
        className="
          min-w-full
          border-collapse
        "
      >

        <thead>

          <tr
            className="
              bg-gray-100
            "
          >

            <th className="border p-3">
              Clause
            </th>

            <th className="border p-3">
              Requirement
            </th>

            <th className="border p-3">
              RAG
            </th>

            <th className="border p-3">
              Risk
            </th>

            <th className="border p-3">
              Rationale
            </th>

            <th className="border p-3">
              Mitigation
            </th>

            <th className="border p-3">
              Evidence
            </th>

          </tr>

        </thead>

        <tbody>

          {
            rows.map(
              (
                row,
                index
              ) => (

                <tr key={index}>

                  <td className="border p-3">
                    {row.clause}
                  </td>

                  <td className="border p-3">
                    {row.requirement}
                  </td>

                  <td className="border p-3">

                    {
                      row.rag === "Red"
                      ? (
                        <span
                          className="
                            text-red-700
                            font-semibold
                          "
                        >
                          🔴 Red
                        </span>
                      )
                      : row.rag === "Amber"
                      ? (
                        <span
                          className="
                            text-yellow-600
                            font-semibold
                          "
                        >
                          🟠 Amber
                        </span>
                      )
                      : (
                        <span
                          className="
                            text-green-700
                            font-semibold
                          "
                        >
                          🟢 Green
                        </span>
                      )
                    }

                  </td>

                  <td className="border p-3">
                    {row.risk}
                  </td>

                  <td className="border p-3">
                    {row.rationale}
                  </td>

                  <td className="border p-3">
                    {row.mitigation}
                  </td>

                  <td className="border p-3">
                    {row.evidence}
                  </td>

                </tr>

              )
            )
          }

        </tbody>

      </table>

    </div>

  )

}