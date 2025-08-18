import asyncio
import random
import time
from sklearn.linear_model import LinearRegression
import numpy as np

class PixieWorker:
    def __init__(self):
        # Initial poll interval and counters for jobs and errors.
        self.poll_interval = 2.0  # seconds
        self.error_count = 0
        self.job_count = 0
        # List to store historical metrics: each record is (job_count, error_rate, poll_interval)
        self.history = []

        # Initialize a simple linear regression model
        self.model = LinearRegression()

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

    def update_history(self):
        """
        Record current performance metrics into history.
        """
        error_rate = self.error_count / (self.job_count + 1)
        # Store record as (job_count, error_rate, poll_interval)
        self.history.append([self.job_count, error_rate, self.poll_interval])

    def train_model(self):
        """
        Train the ML model on historical performance data.
        Here we use job_count and error_rate as predictors for poll_interval.
        """
        # Require at least 5 records for a meaningful model update.
        if len(self.history) < 5:
            return

        data = np.array(self.history)
        X = data[:, :2]  # predictors: job_count and error_rate
        y = data[:, 2]   # target: poll_interval
        self.model.fit(X, y)
        print(f"[{time.strftime('%X')}] ML model trained on {len(self.history)} records.")

    def predict_poll_interval(self):
        """
        Predict a new poll interval using the ML model.
        Returns current poll_interval if model is not yet trained.
        """
        if len(self.history) < 5:
            return self.poll_interval
        # Use current job_count and error_rate as predictors
        error_rate = self.error_count / (self.job_count + 1)
        X_new = np.array([[self.job_count, error_rate]])
        predicted = self.model.predict(X_new)[0]
        # Ensure the predicted interval is within reasonable bounds (e.g., at least 1 second)
        return max(1.0, predicted)

    async def evolve(self):
        """
        Self-evolution logic that adjusts the poll interval.
        ML is used to predict the optimal poll interval based on performance history.
        """
        self.job_count += 1
        # First, update historical records with the current performance
        self.update_history()

        # Train the ML model with the updated history occasionally
        if self.job_count % 5 == 0:
            self.train_model()

        # Use the ML model to predict a new poll interval
        new_poll_interval = self.predict_poll_interval()
        print(
            f"[{time.strftime('%X')}] Job {self.job_count}: "
            f"Errors: {self.error_count}, New poll interval: {new_poll_interval:.2f} seconds."
        )
        self.poll_interval = new_poll_interval

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
