import asyncio
import sys

from Inference import Inference
from InputStreamGenerator import InputStreamGenerator


async def main():
    inputstream_generator = await InputStreamGenerator(samplerate=16000, blocksize=24678, silence_ratio=1000, adjustment_time=5)
    print("Successfully inputsream generator.")
    await inputstream_generator.set_silence_threshold()
    print("Loading models...")
    wakeword_model = await Inference(model_task="transcribe", model_type="vanilla", model_size="base", device="cuda")
    await wakeword_model.load()
    print("Successfully loaded wakeword model.")
    asr_model = await Inference(model_task="transcribe", model_type="pretrained", model_size="medium", device="cuda")
    await asr_model.load()
    print("Successfully loaded asr model.")
    tts_model = await Inference(model_task="tts", device="cuda")
    await tts_model.load()
    print("Successfully loaded tts model.")
    while True:
        print("Listening...")
        audio_data = await inputstream_generator.process()
        print(audio_data)
        await wakeword_model.run(audio_data=audio_data)
        print(wakeword_model.transcript)
        print(wakeword_model.processed_transcript)
        if "thorsten" in wakeword_model.processed_transcript:
            print("Wakeword detected.")
            audio_data = await inputstream_generator.process()
            await asr_model.run(audio_data=audio_data)
            await tts_model.run(text=asr_model.transcript)
         

if __name__ == '__main__':
    try:
        print("Activating wire...")
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')