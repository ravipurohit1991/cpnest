#! /usr/bin/env python
# coding: utf-8

import multiprocessing as mp
import cProfile
import time

class CPNest(object):
    """
    Class to control CPNest sampler
    """
    def __init__(self,userclass,Nlive=100,output='./',verbose=0,seed=None,maxmcmc=100,Nthreads=1):
        from .sampler import Sampler
        from .NestedSampling import NestedSampler
        self.user=userclass
        if seed is None: self.seed=1234
        else:
            self.seed=seed
        self.NS = NestedSampler(self.user,Nlive=Nlive,output=output,verbose=verbose,seed=self.seed,prior_sampling=False)
        self.Evolver = Sampler(self.user,maxmcmc,verbose=0)
        self.NUMBER_OF_PRODUCER_PROCESSES = Nthreads
        self.NUMBER_OF_CONSUMER_PROCESSES = 1

        self.process_pool = []
        self.ns_lock = mp.Lock()
        self.sampler_lock = mp.Lock()
        self.queue = mp.Queue()
        self.port=5555
        self.authkey = "12345"
        self.ip = "0.0.0.0"


    def run(self):
        for i in range(0,self.NUMBER_OF_PRODUCER_PROCESSES):
            p = mp.Process(target=self.Evolver.produce_sample, args=(self.ns_lock, self.queue, self.NS.jobID, self.NS.logLmin, self.seed+i, self.ip, self.port, self.authkey ))
            self.process_pool.append(p)
        for i in range(0,self.NUMBER_OF_CONSUMER_PROCESSES):
            p = mp.Process(target=self.NS.nested_sampling_loop, args=(self.sampler_lock, self.queue, self.port, self.authkey))
            self.process_pool.append(p)
        for each in self.process_pool:
            each.start()
        for each in self.process_pool:
            each.join()


    def worker_sampler(self,*args):
        cProfile.runctx('self.Evolver.produce_sample(*args)', globals(), locals(), 'prof_sampler.prof')
    
    def worker_ns(self,*args):
        cProfile.runctx('self.NS.nested_sampling_loop(*args)', globals(), locals(), 'prof_nested_sampling.prof')

    def profile(self):
        
        for i in range(0,self.NUMBER_OF_PRODUCER_PROCESSES):
            p = mp.Process(target=self.worker_sampler, args=(self.ns_lock, self.queue, self.NS.jobID, self.NS.logLmin, self.seed+i, self.ip, self.port, self.authkey ))
            self.process_pool.append(p)
        for i in range(0,self.NUMBER_OF_CONSUMER_PROCESSES):
            p = mp.Process(target=self.worker_ns, args=(self.sampler_lock, self.queue, self.port, self.authkey))
            self.process_pool.append(p)
        for each in self.process_pool:
            each.start()


