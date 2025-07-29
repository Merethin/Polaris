import asyncio, logging

logger = logging.getLogger("lib")

def normalize(name: str) -> str:
    return name.lower().replace(" ", "_")

LOWERCASE_WORDS = ["a","an","the","and","but","or","for","nor","on","at","to","in","of"]

def selectiveCapitalize(word: str, index: int) -> str:
    if word in LOWERCASE_WORDS and index != 0:
        return word
    return word.capitalize()

def displayName(id: str) -> str:
    return " ".join([
        selectiveCapitalize(w, i) for i, w in enumerate(id.replace("_", " ").split())
    ])

def handle_task_result(task: asyncio.Task):
    try:
        task.result()
    except asyncio.CancelledError:
        logger.debug("Task was cancelled normally.")
    except Exception as e:
        logger.error(f"Task crashed with exception: {e}")