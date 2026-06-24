import { useState } from "react"
import axios from "axios"

type Message = {

  role: string

  content: string

}

export default function ChatSection() {

  const [
    message,
    setMessage
  ] = useState("")

  const [
    messages,
    setMessages
  ] = useState<Message[]>([])

  const [
    loading,
    setLoading
  ] = useState(false)

  const sendMessage =
    async () => {

      if (
        !message.trim()
      )
        return

      const userMessage = {

        role: "user",

        content: message

      }

      setMessages(
        prev => [
          ...prev,
          userMessage
        ]
      )

      setLoading(true)

      try {

        const response =
          await axios.post(
            "/api/chat/",
            {
              message
            }
          )

        setMessages(
          prev => [

            ...prev,

            {
              role:
                "assistant",

              content:
                response.data.answer
            }

          ]
        )

      }

      catch {

        setMessages(
          prev => [

            ...prev,

            {
              role:
                "assistant",

              content:
                "Error generating response."
            }

          ]
        )

      }

      setMessage("")

      setLoading(false)

    }

  return (

    <div
      className="
        bg-white
        rounded-2xl
        shadow
        mt-6
        overflow-hidden
      "
    >

      <div
        className="
          border-b
          p-4
          font-semibold
          text-lg
        "
      >
        Contract Q&A
      </div>

      <div
        className="
          h-[400px]
          overflow-y-auto
          p-4
          bg-gray-50
        "
      >

        {
          messages.length === 0 && (

            <div
              className="
                text-gray-500
              "
            >
              Ask questions about the uploaded contract.
            </div>

          )
        }

        {
          messages.map(
            (
              msg,
              index
            ) => (

              <div
                key={index}
                className={

                  msg.role === "user"

                  ? "flex justify-end mb-3"

                  : "flex justify-start mb-3"

                }
              >

                <div
                  className={

                    msg.role === "user"

                    ? "bg-black text-white px-4 py-2 rounded-xl max-w-[80%]"

                    : "bg-white border px-4 py-2 rounded-xl max-w-[80%]"

                  }
                >

                  {msg.content}

                </div>

              </div>

            )
          )
        }

        {
          loading && (

            <div
              className="
                text-gray-500
              "
            >
              Thinking...
            </div>

          )
        }

      </div>

      <div
        className="
          border-t
          p-4
          flex
          gap-2
        "
      >

        <input
          value={message}
          onChange={
            (
              e
            ) =>
              setMessage(
                e.target.value
              )
          }
          placeholder="
            Ask a question about the contract...
          "
          className="
            flex-1
            border
            rounded-xl
            px-4
            py-3
          "
        />
        <button
          onClick={
            sendMessage
          }
          className="
            bg-black
            text-white
            px-5
            rounded-xl
          "
        >
          Send
        </button>
      </div>
    </div>
  )
}