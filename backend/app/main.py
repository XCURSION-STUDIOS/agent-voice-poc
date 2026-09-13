from dotenv import load_dotenv

load_dotenv(override=False)

from app.pipeline.voice_pipeline import bot  # noqa: E402


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
