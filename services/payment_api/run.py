import asyncio
import sys

import uvicorn


def main() -> None:
    config = uvicorn.Config("services.payment_api.main:app", host="127.0.0.1", port=8000)
    server = uvicorn.Server(config)

    if sys.platform == "win32":
        asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(server.serve())


if __name__ == "__main__":
    main()
