# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens, trailing-whitespace, arguments-differ
"""Main module to run the FastAPI server."""
import os

import dotenv
import uvicorn

dotenv.load_dotenv('token.env')

if (__name__ == "__main__"):
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=os.environ.get('DEBUG'))
