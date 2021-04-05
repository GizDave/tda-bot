from datetime import datetime, date, timedelta
from time import sleep
from math import floor

import transactionHistory
import streaming

class Scheduler:
	"""
		An automatic clock for signaling market open and close.
		Not implemented for premarket and aftermarket trading.
	"""

	def __init__(self):
		self.market_open = datetime.strptime('9:30', '%H:%M').time()
		self.market_close = datetime.strptime('16:00', '%H:%M').time()
		self.isOnline = False

	def inMarket(self, time=None):
		"""
			Given time, check if time is within market hours.
			If time is not given, the current time is chosen.
		"""
		if not time:
			time = datetime.now().time()
		return time >= self.market_open and time <= self.market_close

	# Putting PC to sleep will affect the timer.
	def time_til_open(self):
		"""
			Return the remaining amount of time till market open as timedelta
		"""
		coming_open = datetime.combine(date.today(), self.market_open)

		# Before today's market open
		if datetime.now() < coming_open:
			return coming_open - datetime.now()
		# During today's market hours
		elif self.inMarket():
			return timedelta()
		# After today's market close
		else:
			coming_open = coming_open + timedelta(days=1)
			# If next day's market open is on Sat. or Sun., increment time to next Mon.'s market open
			coming_open = coming_open + timedelta(days=max(0, coming_open.isoweekday() - 5))
			return coming_open - datetime.now()

	def time_til_close(self):
		"""
			Return the remaining amount of time till market close as timedelta
		"""
		if not self.inMarket():
			return timedelta()
		else:
			return datetime.combine(date.today(), self.market_close) - datetime.today()

	def open(self):
		"""
			Market open operation.
		"""
		print('Market is open.')
		streaming.run(
			datetime.combine(date.today(), self.market_close)
		)

	def close(self):
		"""
			Market close operation.
		"""
		print('Market is closed.')
		transactionHistory.run(
			datetime.combine(date.today(), self.market_open), 
			datetime.combine(date.today(), self.market_close)
		)

	# not tested for concurrency
	def shutdown(self):
		"""
			Terminate Scheduler.run().
		"""
		self.isOnline = False

	def run(self):
		"""
			Run automated routine.
		"""
		self.isOnline = True

		while self.isOnline:
			# outside market hours
			print('Waiting for market open...')
			remaining = self.time_til_open().total_seconds()
			sleep(remaining)
			self.open()

			# during market hours
			remaining = self.time_til_close().total_seconds()
			sleep(remaining)
			self.close()

bot = Scheduler()
bot.run()