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
			self.tx_prbs_config.write(Txval)
			time.sleep(0.001)
		
		if Rxval is not None:
			self.rx_prbs_config.write(Rxval)
			time.sleep(0.001)

	def setErrMask(self,error_fraction,data_width = 20):
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

	def MGTLinerate(self):
		return str(int(self.mgt_linerate.read())/2)

	def BERinit(self):
		self.c1 = 0
		self.c2 = 0
		self.err1 = 0
		self.err2 = 0
		self.enable_err_count.write(0b01)
		time.sleep(0.001)

	def PLLlockStatus(self):
		if(int(self.plllock.read()) == 1):
			return "LOCKED"
		else:
			return "NOT LOCKED"

	def checkMGTLink(self):
		self.checklink.write(1)
		self.checklink.write(0)

		for i in range(10000):
			time.sleep(0.001)
			if(int(self.linkstatus.read()) == 1):
				return "LINK"

		return "NO LINK"


	def phaseAlign(self):
		self.seldata.write(1)
		self.en8b10b.write(1)
		self.input.write(0x001BC)
		self.k.write(0b01)
		self.rx_restart_phaseAlign.write(1)
		self.rx_restart_phaseAlign.write(0)
		for i in range(10000):
			time.sleep(0.001)
			if(int(self.rx_phaseAlign_ack.read()) == 1):
				print("RX Ready. Alignment Done")
				self.seldata.write(0)
				return

		raise TimeoutError

	def drpWrite(self,addr,value):
		self.drp_addr.write(addr)
		self.drp_wren.write(1)
		self.drp_di.write(value)
		self.drp_oprenable.write(1)

		if(int(self.rx_reset_ack.read()) == 0 | int(self.rx_phaseAlign_ack.read()) == 0):
			raise ValueError("RX reset in progress. Cannot use DRP now")

		for i in range(10000):
			time.sleep(0.001)
			if(int(self.drp_ack.read()) == 1):
				self.drp_oprenable.write(0)
				print("DRP write complete")
				return

		raise TimeoutError

	def drpRead(self,addr):
		self.drp_addr.write(addr)
		self.drp_wren.write(0)
		self.drp_oprenable.write(1)
		drp_read_value = 0

		if(int(self.rx_reset_ack.read()) == 0 | int(self.rx_phaseAlign_ack.read()) == 0):
			raise ValueError("RX reset in progress. Cannot use DRP now")

		for i in range(10000):
			time.sleep(0.001)
			if(int(self.drp_ack.read()) == 1):
				self.drp_oprenable.write(0)
				drp_read_value = int(self.drp_value.read())
				return drp_read_value

		raise TimeoutError

	def txPolarity(self,invert=False):
		if invert == True:
			self.tx_polarity.write(1)
			self.resetTx()
			self.resetRx()
			self.phaseAlign()
			time.sleep(0.001)
		else:
			self.tx_polarity.write(0)
			self.resetTx()
			self.resetRx()
			self.phaseAlign()
			time.sleep(0.001)

	def rxPolarity(self,invert=False):
		if invert == True:
			self.rx_polarity.write(1)
			self.resetTx()
			self.resetRx()
			self.phaseAlign()
			time.sleep(0.001)
		else:
			self.rx_polarity.write(0)
			self.resetTx()
			self.resetRx()
			self.phaseAlign()
			time.sleep(0.001)

	def enableLoopback(self):
		self.loopback.write(0b010)
		self.resetTx()
		self.resetRx()
		self.phaseAlign()
		time.sleep(0.001)

	def disableLoopback(self):
		self.loopback.write(0b000)
		self.resetTx()
		self.resetRx()
		self.phaseAlign()
		time.sleep(0.001)

	def resetTx(self):
		self.tx_reset_host.write(1)
		self.tx_reset_host.write(0)

		for i in range(10000):
			time.sleep(0.001)
			if(int(self.tx_reset_ack.read()) == 1):
				print("TX Reset Complete")
				return
			
		raise TimeoutError

	def resetRx(self):
		self.rx_reset_host.write(1)
		self.rx_reset_host.write(0)

		for i in range(10000):
			time.sleep(0.001)
			if(int(self.rx_reset_ack.read()) == 1):
				print("RX Reset Complete")
				return

		raise TimeoutError

	def changeOutputSwing(self,value=0b1000):
		if value > 15:
			raise ValueError("Please enter a 4 bit number") 

		self.diffctrl.write(value)
		time.sleep(0.001)

	def changetxPrecursor(self,value=0b00000):
		if value > 31:
			raise ValueError("Please enter a 5 bit number") 

		self.txprecursor.write(value)
		time.sleep(0.001)

	def changetxPostcursor(self,value=0b00000):
		if value > 31:
			raise ValueError("Please enter a 4 bit number") 

		self.txpostcursor.write(value)
		time.sleep(0.001)

	def calcBER(self, data_width = 20):

		self.enable_err_count.write(0b11)
		self.err2 = err2 = int(self.global_error.read())
		self.c2 = c2 = int(self.total_bit_count.read())

		ber = ((self.err2-self.err1)/(data_width*(self.c2-self.c1)))

		self.enable_err_count.write(0b00)
		time.sleep(0.001)
		self.enable_err_count.write(0b11)

		self.c1 = c1 = int(self.total_bit_count.read())
		self.err1 = err1 = int(self.global_error.read())

		self.enable_err_count.write(0b01)
		return ber
		

#Use CalcBER below if using only abstraction class without GUI.

	def calcBERabs(self,timems, data_width = 20):
		self.seldata.write(0)
		self.enable_err_count.write(0b00)
		time.sleep(0.001)
		self.enable_err_count.write(0b11)

		c1 = int(self.total_bit_count.read())
		err1 = int(self.global_error.read())

		self.enable_err_count.write(0b01)
		time.sleep(timems*0.001)
		self.enable_err_count.write(0b11)

		err2 = int(self.global_error.read())
		c2 = int(self.total_bit_count.read())

		print(c1,err1,c2,err2)

		ber = ((err2-err1)/(data_width*(c2-c1)))
		return ber





