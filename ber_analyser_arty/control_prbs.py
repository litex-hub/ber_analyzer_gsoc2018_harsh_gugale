import time

class PRBSControl:
	def __init__ (self,regs,name):
		self.regs = regs
		self.name = name
		self.build()

	def build(self):
		for key, value in self.regs.d.items():
			if self.name == key[:len(self.name)]:
				key = key.replace(self.name + "_", "")
				setattr(self, key, value)

	def setPRBSConfig(self,txConfig,rxConfig):
		Txval = 0
		Rxval = 0
		if txConfig is 7:
			Txval = 0b00
		elif txConfig is 15:
			Txval = 0b01
		elif txConfig is 23:
			Txval = 0b10
		elif txConfig is 31:
			Txval = 0b11
		else:
			Txval = None

		if rxConfig is 7:
			Rxval = 0b00
		elif rxConfig is 15:
			Rxval = 0b01
		elif rxConfig is 23:
			Rxval = 0b10
		elif rxConfig is 31:
			Rxval = 0b11
		else:
			Rxval = None

		if Txval is not None: 
			self.tx_config.write(Txval)
			time.sleep(0.001)
		
		if Rxval is not None:
			self.rx_config.write(Rxval)
			time.sleep(0.001)

	def setErrMask(self,error_fraction,data_width = 40):
		mask = 0
		maskval = 0
		if error_fraction not in [0,0.25,0.5,0.75,1]:
			raise ValueError("Error Fraction can only be in [0,0.25,0.5,0.75,1]") 

		else:
			if error_fraction == 0:
				maskval = 0b0000
			elif error_fraction == 0.25:
				maskval = 0b0001
			elif error_fraction == 0.5:
				maskval = 0b0101
			elif error_fraction == 0.75:
				maskval = 0b0111
			elif error_fraction == 1:
				maskval = 0b1111

			for i in range(int(data_width/4)):
				mask = mask <<4
				mask = mask + maskval
				
			self.mask.write(mask)
			time.sleep(0.001)

	def enable8b10b(self):
		self.en8b10b.write(0x01)
		time.sleep(0.001)

	def disable8b10b(self):
		self.en8b10b.write(0x00)
		time.sleep(0.001)


	def BERinit(self):
		self.c1 = 0
		self.c2 = 0
		self.err1 = 0
		self.err2 = 0
		self.enable_err_count.write(0b01)
		time.sleep(0.001)

	def calcBER(self, data_width = 40):

		self.enable_err_count.write(0b11)
		self.err2 = err2 = int(self.global_error.read())
		self.c2 = c2 = int(self.total_bit_count.read())

		if(int(self.en8b10b.read()) == 1):
			ber = ((self.err2-self.err1)/((data_width/10)*8*(self.c2-self.c1)))
		else:
			ber = ((self.err2-self.err1)/(data_width*(self.c2-self.c1)))

		self.enable_err_count.write(0b00)
		time.sleep(0.001)
		self.enable_err_count.write(0b11)

		self.c1 = c1 = int(self.total_bit_count.read())
		self.err1 = err1 = int(self.global_error.read())

		self.enable_err_count.write(0b01)
		return ber
		

#Use CalcBER below if using only abstraction class without GUI.

	# def calcBER(self,timems, data_width = 40):
	# 	self.enable_err_count.write(0b00)
	# 	time.sleep(0.001)
	# 	self.enable_err_count.write(0b11)

	# 	c1 = int(self.total_bit_count.read())
	# 	err1 = int(self.global_error.read())

	# 	self.enable_err_count.write(0b01)
	# 	time.sleep(timems*0.001)
	# 	self.enable_err_count.write(0b11)

	# 	err2 = int(self.global_error.read())
	# 	c2 = int(self.total_bit_count.read())

	# 	if(int(self.en8b10b.read()) == 1):
	# 		ber = ((err2-err1)/((data_width/10)*8*(c2-c1)))
	# 	else:
	# 		ber = ((err2-err1)/(data_width*(c2-c1)))
	# 	return ber





