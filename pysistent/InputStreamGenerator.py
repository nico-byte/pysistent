import numpy as np
import sounddevice as sd
import asyncio
import warnings

from async_class import AsyncClass


class InputStreamGenerator(AsyncClass):
    """
    Represents a generator that produces an input stream of audio data.
    https://github.com/tobiashuttinger/openai-whisper-realtime/blob/main/openai-whisper-realtime.py
    """
    async def __ainit__(self, samplerate: int, blocksize: int, silence_ratio: int, adjustment_time: int, silence_threshold: int):
        self.SAMPLERATE = samplerate
        self.BLOCKSIZE = blocksize
        self.SILENCE_RATIO = silence_ratio
        self.ADJUSTMENT_TIME = adjustment_time
        self.SILENCE_THRESHOLD = silence_threshold
        
        self.global_ndarray = None
        self.temp_ndarray = None

    async def generate(self):
        """
        This asynchronous generator function initiates an audio input stream with the specified sample rate and block size,
        using sounddevice. It continuously reads audio data into a queue in a non-blocking manner and yields the data along with its status
        whenever available. This function is designed to be used in an asynchronous context to facilitate real-time audio processing tasks.
        """
        q_in = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def callback(in_data, _, __, state):
            loop.call_soon_threadsafe(q_in.put_nowait, (in_data.copy(), state))

        stream = sd.InputStream(samplerate=self.SAMPLERATE, channels=1, dtype='int16', blocksize=self.BLOCKSIZE, callback=callback)
        with stream:
            while True:
                indata, status = await q_in.get()
                yield indata, status
        
    async def set_silence_threshold(self):
        """
        This asynchronous method dynamically adjusts the silence threshold based on the loudness of the initial 
        audio input. It processes a predefined duration of audio to calculate an average loudness value, which 
        is then used to set the silence threshold. This adjustment is crucial for optimizing subsequent voice 
        activity detection and ensuring the system's sensitivity is tailored to the current environment's noise level. 
        A warning is issued if the calculated threshold is exceptionally high, indicating potential issues with 
        microphone input levels or environmental noise.
        """
        blocks_processed = 0
        loudness_values = []

        async for indata, _ in self.generate():
            blocks_processed += 1
            indata_flattened = abs(indata.flatten())

            # Compute loudness over first few seconds to adjust silence threshold
            loudness_values.append(np.mean(indata_flattened))

            # Stop recording after ADJUSTMENT_TIME seconds
            if blocks_processed >= self.ADJUSTMENT_TIME * self.SAMPLERATE / self.BLOCKSIZE:
                self.SILENCE_THRESHOLD = int((np.mean(loudness_values) * self.SILENCE_RATIO) / 15)
                break
            
        print(f'\nSet SILENCE_THRESHOLD to {self.SILENCE_THRESHOLD}\n')