import asyncio
import random
import time

class PixieWorker:
    def __init__(self):
        # Initial poll interval and counters for jobs and errors.
        self.poll_interval = 2.0  # seconds
        self.error_count = 0
        self.job_count = 0

    async def promise(self):
        """
        Simulates an asynchronous job promise.
        The worker waits for a duration defined by the poll interval.
        There's a simulated 20% chance for the job to fail.
        """
        await asyncio.sleep(self.poll_interval)
        if random.random() < 0.2:
            raise Exception("Job failed due to simulated error.")
        return "Job succeeded"

    async def run_job(self):
        """
        Attempts to run a job promise and prints the result.
        Increments the error counter if the job fails.
        """
        try:
            result = await self.promise()
            print(f"[{time.strftime('%X')}] Job result: {result}")
        except Exception as e:
            self.error_count += 1
            print(f"[{time.strftime('%X')}] Error during job run: {e}")

    async def evolve(self):
        """
        Self-evolution logic that adjusts the poll interval based on error rate.
        A high error rate leads to a longer poll interval to reduce load,
        whereas a low error rate shortens the interval for faster job processing.
        """
        self.job_count += 1
        error_rate = self.error_count / (self.job_count + 1)
        print(f"[{time.strftime('%X')}] Job {self.job_count} error rate: {error_rate:.2f}")

        # Adjust poll_interval based on error rate.
        if error_rate > 0.1:
            # Increase the interval if errors are high.
            self.poll_interval += 0.5
            print(f"[{time.strftime('%X')}] High error rate: Increasing poll interval to {self.poll_interval:.2f} seconds.")
        else:
            # Decrease the interval if errors are low, with a lower bound of 1 second.
            self.poll_interval = max(1, self.poll_interval - 0.2)
            print(f"[{time.strftime('%X')}] Low error rate: Decreasing poll interval to {self.poll_interval:.2f} seconds.")

    async def run(self):
        """
        Main loop for the PixieWorker: run a job and then evolve based on performance.
        This loop runs indefinitely.
        """
        while True:
            await self.run_job()
            await self.evolve()

async def main():
    worker = PixieWorker()
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
