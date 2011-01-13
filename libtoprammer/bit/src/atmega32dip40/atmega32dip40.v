/*
 *   TOP2049 Open Source programming suite
 *
 *   Atmel Mega32 DIP40
 *   FPGA bottomhalf implementation
 *
 *   Copyright (c) 2010-2011 Michael Buesch <mb@bu3sch.de>
 *
 *   This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation; either version 2 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License along
 *   with this program; if not, write to the Free Software Foundation, Inc.,
 *   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */

/* The runtime ID and revision. */
`define RUNTIME_ID	16'h0004
`define RUNTIME_REV	16'h01

module atmega32dip40(data, ale, write, read, zif);
	inout [7:0] data;
	input ale;
	input write;
	input read;
	inout [48:1] zif;

	reg [7:0] address;
	reg [7:0] read_data;
	wire read_oe;

	/* Signals to/from the DUT */
	reg dut_oe, dut_wr, dut_xtal, dut_pagel;
	reg dut_bs1, dut_bs2;
	reg dut_xa0, dut_xa1;
	reg [7:0] dut_data;
	reg dut_vpp_en;
	reg dut_vpp;
	reg dut_vcc_en;
	reg dut_vcc;

	/* Constant lo/hi */
	wire low, high;
	assign low = 0;
	assign high = 1;

	initial begin
		address <= 0;
		read_data <= 0;
		dut_oe <= 0;
		dut_wr <= 0;
		dut_xtal <= 0;
		dut_pagel <= 0;
		dut_bs1 <= 0;
		dut_bs2 <= 0;
		dut_xa0 <= 0;
		dut_xa1 <= 0;
		dut_data <= 0;
		dut_vpp_en <= 0;
		dut_vpp <= 0;
		dut_vcc_en <= 0;
		dut_vcc <= 0;
	end

	always @(negedge ale) begin
		address <= data;
	end

	always @(posedge write) begin
		case (address)
		8'h10: begin
			/* Data write */
			dut_data <= data;
		end
		8'h11: begin /* VCC/VPP control */
			dut_vpp_en <= data[0];
			dut_vpp <= data[1];
			dut_vcc_en <= data[2];
			dut_vcc <= data[3];
		end
		8'h12: begin
			/* Control pin access */
			case (data[6:0])
			1: begin
				/* Unused */
			end
			2: begin
				dut_oe <= data[7];
			end
			3: begin
				dut_wr <= data[7];
			end
			4: begin
				dut_bs1 <= data[7];
			end
			5: begin
				dut_xa0 <= data[7];
			end
			6: begin
				dut_xa1 <= data[7];
			end
			7: begin
				dut_xtal <= data[7];
			end
			8: begin
				/* Unused */
			end
			9: begin
				dut_pagel <= data[7];
			end
			10: begin
				dut_bs2 <= data[7];
			end
			endcase
		end
		endcase
	end

	always @(negedge read) begin
		case (address)
		8'h10: begin
			/* Data read */
			read_data <= zif[32:25];
		end
		8'h12: begin
			/* Status read */
			read_data[0] <= zif[39];	/* RDY */
			read_data[7:1] <= 0;
		end

		8'hFD: read_data <= `RUNTIME_ID & 16'hFF;
		8'hFE: read_data <= (`RUNTIME_ID >> 8) & 16'hFF;
		8'hFF: read_data <= `RUNTIME_REV;
		endcase
	end

	assign read_oe = !read && address[4];

	bufif0(zif[1], low, low);
	bufif0(zif[2], low, low);
	bufif0(zif[3], low, low);
	bufif0(zif[4], low, low);
	bufif0(zif[5], dut_pagel, low);		/* PD7, PAGEL */
	bufif0(zif[6], low, high);		/* PC0 */
	bufif0(zif[7], low, high);		/* PC1 */
	bufif0(zif[8], low, high);		/* PC2 */
	bufif0(zif[9], low, high);		/* PC3 */
	bufif0(zif[10], low, high);		/* PC4 */
	bufif0(zif[11], low, high);		/* PC5 */
	bufif0(zif[12], low, high);		/* PC6 */
	bufif0(zif[13], low, high);		/* PC7 */
	bufif0(zif[14], dut_vcc, !dut_vcc_en);	/* AVCC */
	bufif0(zif[15], low, low);		/* GND */
	bufif0(zif[16], low, high);		/* AREF */
	bufif0(zif[17], low, high);		/* PA7 */
	bufif0(zif[18], low, high);		/* PA6 */
	bufif0(zif[19], low, high);		/* PA5 */
	bufif0(zif[20], low, high);		/* PA4 */
	bufif0(zif[21], low, high);		/* PA3 */
	bufif0(zif[22], low, high);		/* PA2 */
	bufif0(zif[23], low, high);		/* PA1 */
	bufif0(zif[24], dut_bs2, low);		/* PA0, BS2 */
	bufif0(zif[25], dut_data[0], !dut_oe);	/* PB0, DATA0 */
	bufif0(zif[26], dut_data[1], !dut_oe);	/* PB1, DATA1 */
	bufif0(zif[27], dut_data[2], !dut_oe);	/* PB2, DATA2 */
	bufif0(zif[28], dut_data[3], !dut_oe);	/* PB3, DATA3 */
	bufif0(zif[29], dut_data[4], !dut_oe);	/* PB4, DATA4 */
	bufif0(zif[30], dut_data[5], !dut_oe);	/* PB5, DATA5 */
	bufif0(zif[31], dut_data[6], !dut_oe);	/* PB6, DATA6 */
	bufif0(zif[32], dut_data[7], !dut_oe);	/* PB7, DATA7 */
	bufif0(zif[33], dut_vpp, !dut_vpp_en);	/* /RESET */
	bufif0(zif[34], dut_vcc, !dut_vcc_en);	/* VCC */
	bufif0(zif[35], low, low);		/* GND */
	bufif0(zif[36], low, high);		/* XTAL2 */
	bufif0(zif[37], dut_xtal, low);		/* XTAL1 */
	bufif0(zif[38], low, high);		/* PD0 */
	bufif0(zif[39], low, high);		/* PD1, RDY/BSY */
	bufif0(zif[40], dut_oe, low);		/* PD2, /OE */
	bufif0(zif[41], dut_wr, low);		/* PD3, /WR */
	bufif0(zif[42], dut_bs1, low);		/* PD4, BS1 */
	bufif0(zif[43], dut_xa0, low);		/* PD5, XA0 */
	bufif0(zif[44], dut_xa1, low);		/* PD6, XA1 */
	bufif0(zif[45], low, low);
	bufif0(zif[46], low, low);
	bufif0(zif[47], low, low);
	bufif0(zif[48], low, low);

	bufif1(data[0], read_data[0], read_oe);
	bufif1(data[1], read_data[1], read_oe);
	bufif1(data[2], read_data[2], read_oe);
	bufif1(data[3], read_data[3], read_oe);
	bufif1(data[4], read_data[4], read_oe);
	bufif1(data[5], read_data[5], read_oe);
	bufif1(data[6], read_data[6], read_oe);
	bufif1(data[7], read_data[7], read_oe);
endmodule
