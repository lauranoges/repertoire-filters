#!/usr/bin/env python
import csv
import sys
csv.field_size_limit(sys.maxsize)  # make sure we can write very large csv fields
import argparse
import numpy
from Bio.Seq import Seq

partis_path = '.'  # edit this if you're not running from the main partis dir
sys.path.insert(1, partis_path + '/python')
import utils
import glutils
from clusterpath import ClusterPath

parser = argparse.ArgumentParser()
parser.add_argument('--infile')
parser.add_argument('--locus')
parser.add_argument('--param')
args = parser.parse_args()

glfo = glutils.read_glfo(args.param + '/hmm/germline-sets', locus=args.locus)

cp = ClusterPath()
cp.readfile(args.infile)
best_partition = cp.partitions[cp.i_best]
# sorted_clusters = sorted(best_partition, key=len, reverse=True)  # sort by size

# clonal family attributes to print
def print_sizeindex(cluster):
    cluster_index = sorted_clusters.index(cluster)
    print 'cluster index =', cluster_index

def print_stuff(line):
    print line['v_gene'],
    print line['d_gene'],
    print line['j_gene']
    print len(line['unique_ids']), 'sequences in cluster'
    print getkey(line['unique_ids'])
    print float(len(cluster)) / n_total, 'fraction of total repertoire'
    print 'number of mutations per sequence in cluster', sorted(line['n_mutations'])
    print numpy.mean(line['n_mutations']), 'mean number of mutations'
    print numpy.median(line['n_mutations']), 'median number of mutations'
    print len(line['naive_seq']), 'length of naive seq'
    print numpy.mean(line['mut_freqs']), 'mean SHM'
    # print numpy.mean(line['n_mutations'])/len(line['naive_seq']), 'mean % SHM' <--this approach does NOT yield exactly same value as above
    print line['cdr3_length'], 'CDR3 length in nts'
    cdr3_seq = line['naive_seq'][(line['codon_positions']['v']):((line['codon_positions']['j'])+3)] #get nt sequence of CDR3 from first base of cysteine through last base of tryptophan
    print Seq(cdr3_seq).translate()
    print utils.fay_wu_h(line, debug=True), 'SFS (Fay Wu H) score' # site frequency spectrum
    utils.print_reco_event(utils.synthesize_single_seq_line(line, iseq=0))  # print ascii-art representation of the rearrangement event
    print

# formatting necessity
def getkey(uid_list):
    return ':'.join(uid_list)

# creates a dictionary with keys = unique_ids and values = annotations
annotations = {}
with open(args.infile.replace('.csv', '-cluster-annotations.csv')) as csvfile:
    reader = csv.DictReader(csvfile)
    for line in reader:  # there's a line for each cluster
        if line['v_gene'] == '':  # failed (i.e. couldn't find an annotation)
            continue
        utils.process_input_line(line)  # converts strings in the csv file to floats/ints/dicts/etc.
        utils.add_implicit_info(glfo, line)  # add stuff to <line> that's useful, isn't written to the csv since it's redundant
        # utils.print_reco_event(line)  # print ascii-art representation of the rearrangement event
        annotations[getkey(line['unique_ids'])] = line


# sort by size
sorted_clusters = sorted(annotations, key=lambda q: len(annotations[q]['unique_ids']), reverse=True)
n_total = sum([len(cluster) for cluster in sorted_clusters])

# add more criteria
biggest_clusters = sorted_clusters[:100] # 100 biggest clusters
shm_clusters = sorted(biggest_clusters, key=lambda q: numpy.mean(annotations[q]['mut_freqs']), reverse=True)
sfs_clusters = sorted(biggest_clusters, key=lambda q: utils.fay_wu_h(annotations[q], debug=False))

# cluster size: print x biggest clusters
print '\x1b[1;32;40m' + '  printing the largest clusters' + '\x1b[0m'
for cluster in sorted_clusters[:5]:
    print_sizeindex(cluster)
    print_stuff(annotations[cluster])

# high mean %SHM: print most mutated clusters from 100 biggest clusters
print '\x1b[1;32;40m' + '  printing the most mutated clusters (within 100 biggest)' + '\x1b[0m'
for cluster in shm_clusters[:5]:
    print_sizeindex(cluster)
    print_stuff(annotations[cluster])

# Highest SFS Fay Wu H scores
print '\x1b[1;32;40m' + '  printing clusters with high SFS (within 100 biggest)' + '\x1b[0m'
for cluster in sfs_clusters[:5]:
    print_sizeindex(cluster)
    print_stuff(annotations[cluster])

# published bnAb VH gene usage (Yu and Guan, Frontiers in Immunology, 2014)
cd4bs_genes = ['IGHV1-2', 'IGHV1-46', 'IGHV1-3', 'IGHV4-61']
glycan_genes = ['IGHV3-21', 'IGHV1-8', 'IGHV3-20', 'IGHV3-33', 'IGHV4-39', 'IGHV4-59', 'IGHV4-4']
bridging_genes = ['IGHV1-3', 'IGHV3-30']
mper_genes = ['IGHV1-69', 'IGHV2-5', 'IGHV3-15', 'IGHV5-51']

# CD4bs bnAb VH gene usage
def boolfunc(q):
    if (annotations[cluster]['v_gene']).split('*')[0] not in cd4bs_genes:
        return False
    if annotations[cluster]['cdr3_length'] > 75 or annotations[cluster]['cdr3_length'] < 30:
        return False
    return True

interesting_clusters = [cluster for cluster in sorted_clusters if boolfunc(cluster)]
print '\x1b[1;32;40m' + '  found %d cd4bs clusters, printing the 5 largest hits' % len(interesting_clusters)
sorted_interesting = sorted(interesting_clusters, key=lambda q: len(annotations[q]['unique_ids']), reverse=True)
for cluster in sorted_interesting[0:5]: # five biggest cd4bs clusters
    print_sizeindex(cluster)
    print_stuff(annotations[cluster])


# glycan epitope bnAb VH gene usage
def boolfunc(q):
    if (annotations[cluster]['v_gene']).split('*')[0] not in glycan_genes:
        return False
    if annotations[cluster]['cdr3_length'] < 60:
        return False
    return True

interesting_clusters = [cluster for cluster in sorted_clusters if boolfunc(cluster)]
print '\x1b[1;32;40m' + '  found %d glycan clusters, printing the 5 largest hits' % len(interesting_clusters)
sorted_interesting = sorted(interesting_clusters, key=lambda q: len(annotations[q]['unique_ids']), reverse=True)
for cluster in sorted_interesting[0:5]: # five biggest cd4bs clusters
    print_sizeindex(cluster)
    print_stuff(annotations[cluster])


# bridging region epitope bnAb VH gene usage
def boolfunc(q):
    if (annotations[cluster]['v_gene']).split('*')[0] not in bridging_genes:
        return False
    if annotations[cluster]['cdr3_length'] < 66:
        return False
    return True

interesting_clusters = [cluster for cluster in sorted_clusters if boolfunc(cluster)]
print '\x1b[1;32;40m' + '  found %d bridging region clusters, printing the 5 largest hits' % len(interesting_clusters)
sorted_interesting = sorted(interesting_clusters, key=lambda q: len(annotations[q]['unique_ids']), reverse=True)
for cluster in sorted_interesting[0:5]: # five biggest cd4bs clusters
    print_sizeindex(cluster)
    print_stuff(annotations[cluster])


# mper region epitope bnAb VH gene usage
def boolfunc(q):
    if (annotations[cluster]['v_gene']).split('*')[0] not in mper_genes:
        return False
    if annotations[cluster]['cdr3_length'] < 60:
        return False
    return True

interesting_clusters = [cluster for cluster in sorted_clusters if boolfunc(cluster)]
print '\x1b[1;32;40m' + '  found %d mper region clusters, printing the 5 largest hits' % len(interesting_clusters)
sorted_interesting = sorted(interesting_clusters, key=lambda q: len(annotations[q]['unique_ids']), reverse=True)
for cluster in sorted_interesting[0:5]: # five biggest cd4bs clusters
    print_sizeindex(cluster)
    print_stuff(annotations[cluster])


sys.exit()