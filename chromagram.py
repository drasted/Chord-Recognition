"""
Algorithm based on the paper 'Automatic Chord Recognition from
Audio Using Enhanced Pitch Class Profile' by Kyogu Lee
This script computes 12 dimensional chromagram for chord detection
@author ORCHISAMA
"""

from __future__ import division
from scipy.signal import hamming
from scipy.fftpack import fft
import numpy as np
import matplotlib.pyplot as plt

def nearestPow2(inp):
    power = np.ceil(np.log2(inp))
    return 2**power

"""Function to calculcate Harmonic Power Spectrum from DFT"""
def HPS(dft,M):

	hps_len = int(np.ceil(np.size(dft)/(2**M)))
 	hps = np.ones(hps_len)
 	for n in range(hps_len):
 		for m in range(M+1): 
 			hps[n] *= np.absolute(dft[(2**m)*n])
 	return hps	


"""Function to compute CQT using sparse matrix multiplication, Brown and Puckette 1992- fast"""	
def CQT_fast(x,fs,bins,fmin,fmax,M):

	threshold = 0.0054 #for Hamming window
	K = int(bins*np.ceil(np.log2(fmax/fmin)))
	Q = 1/(2**(1/bins)-1)
	nfft = np.int32(nearestPow2(np.ceil(Q*fs/fmin)))
	tempKernel = np.zeros(nfft, dtype = np.complex)
	specKernel = np.zeros(nfft, dtype = np.complex)
	sparKernel = []

	#create sparse Kernel 
	for k in range(K-1,-1,-1):
		fk = (2**(k/bins))*fmin
		N = np.int32(np.round((Q*fs)/fk))
		tempKernel[:N] = hamming(N)/N * np.exp(-2*np.pi*1j*Q*np.arange(N)/N)
		specKernel = fft(tempKernel)
		specKernel[np.where(np.abs(specKernel) <= threshold)] = 0
		if k == K-1:
			sparKernel = specKernel
		else:
			sparKernel = np.vstack((specKernel, sparKernel))
	
	sparKernel = np.transpose(np.conjugate(sparKernel))/nfft
	ft = fft(x,nfft)
	cqt = np.dot(ft, sparKernel)
	ft = fft(x,nfft*(2**M))
	#calculate harmonic power spectrum
	# harm_pow = HPS(ft,M)
	# cqt = np.dot(harm_pow, sparKernel)
	return cqt


"""Function to compute constant Q Transform, Judith Brown, 1991 - slow"""
def CQT_slow(x, fs, bins, fmin, fmax):
	
	K = int(bins*np.ceil(np.log2(fmax/fmin)))
	Q = 1/(2**(1/bins)-1)
	cqt = np.zeros(K, dtype = np.complex)

	for k in range(K):
		fk = (2**(k/bins))*fmin
		N = int(np.round(Q*fs/fk))
		arr = -2*np.pi*1j*Q*np.arange(N)/N 
		cqt[k] = np.dot(x[:N], np.transpose(hamming(N) * np.exp(arr)))/N 
	return cqt


"""Function to compute Pitch Class Profile from constant Q transform"""
def PCP(cqt,bins,M):
	CH = np.zeros(bins)
	for b in range(bins):
		CH[b] = np.sum(cqt[b + (np.arange(M)*bins)])
	return CH


def compute_chroma(s,fs):
#downsample sampling frequency to 11025Hz
	x = s[::4]
	x = x[:,1]
	fs = int(fs/4)

	#framing audio, window length = 8192, hop size = 1024
	nfft = 8192
	hop_size = 1024
	nFrames = int(np.round(len(x)/(nfft-hop_size)))
	#zero padding to make signal length long enough to have nFrames
	x = np.append(x, np.zeros(nfft))
	xFrame = np.empty((nfft, nFrames))
	start = 0    
	for n in range(nFrames):
		xFrame[:,n] = x[start:start+nfft] 
		start = start + nfft - hop_size 

	fmin = 96
	fmax = 5250
	bins = 12
	M = 3
	nOctave = np.int32(np.ceil(np.log2(fmax/fmin)))
	CH = np.empty((bins,nFrames))
	for n in range(nFrames):
		#compute constant Q transform
		cqt_fast = CQT_fast(xFrame[:,n],fs,bins,fmin,fmax,M)
		plt.figure(1)
		plt.plot(np.absolute(cqt_fast))
		#compute pitch class profile
		CH[:,n] = PCP(np.absolute(cqt_fast), bins, nOctave)
		plt.figure(2)
		plt.plot(CH[:,n])

	plt.figure(1)
	plt.xlabel('Bin Number')
	plt.ylabel('Magnitude of Q transform')
	plt.title('CQT')

	plt.figure(2)
	notes = ['G','G#','A','A#','B','C','C#','D','D#','E','F','F#']
	plt.xticks(np.arange(bins),notes)
	plt.title('Pitch Class Profile')
	plt.xlabel('Note')

	#averaged and normalized chromagram
	chroma = np.mean(CH,axis = 1)
	chroma /= np.max(chroma)
	plt.figure(3)
	plt.plot(chroma)
	plt.xticks(np.arange(bins),notes)
	plt.title('Averaged PCP')
	plt.xlabel('Note')
	plt.show()

	return chroma

