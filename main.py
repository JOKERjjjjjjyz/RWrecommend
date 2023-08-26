import dataloader
import world
import torch
from dataloader import Loader
import sys
import scipy.sparse as sp
from train import *
import numpy as np
from scipy.sparse import csr_matrix


if world.dataset in ['gowalla', 'yelp2018', 'amazon-book']:
    dataset = dataloader.Loader(path="./data")
elif world.dataset == 'lastfm':
    dataset = dataloader.Loader(path="./data")

num_rows, num_cols = dataset.UserItemNet.shape
vector_origin = []

# 遍历每一行
for row_idx in range(num_rows):
    # 获取当前行的起始和结束索引
    start_idx = dataset.UserItemNet.indptr[row_idx]
    end_idx = dataset.UserItemNet.indptr[row_idx + 1]

    # 获取当前行的列索引和对应的非零元素
    row_indices = dataset.UserItemNet.indices[start_idx:end_idx]
    row_data = dataset.UserItemNet.data[start_idx:end_idx]

    # 初始化一个零向量
    row_vector = np.zeros(num_cols)

    # 将非零元素赋值给向量的相应位置
    for col_idx, value in zip(row_indices, row_data):
        row_vector[col_idx] = value

    # 将当前行向量添加到向量数组中
    vector_origin.append(row_vector)

# 将向量数组转换为 NumPy 数组
vector_array = np.array(vector_origin)

graph = dataset.getSparseGraph()
graph = graph.tocsr()

# M:user number; N: item number
# vector_origin: M*N;  vector_propagate: (M+N)*N
M = dataset.n_users
N = dataset.m_items
vector_propagate = [np.zeros(N) for _ in range(M + N)]
K = int(world.topks)

for i in range(1,K+1):
    sampleNum = Klayer_sampleNum(i,0.025, 0.5, M)
    vector_propagate = propagate(i,graph,vector_origin,vector_propagate,M,N,sampleNum)

recommendList,recommend_vector = topK(vector_origin,vector_propagate,M,N,20)
sp.save_npz(dataset.path + '/recommend_vector.npz', recommend_vector)
count = evaluate(recommendList , dataset.test)
recall = count / dataset.testDataSize
print ("recall:",recall)
# dense_array = dataset.UserItemNet.toarray()

# 将原始 stdout 保存到变量
original_stdout = sys.stdout

# 打开一个文件来替代 stdout
with open('output.txt', 'w') as f:
    # 重定向 stdout 到文件
    sys.stdout = f

    # 现在所有的 print 输出都会写入到文件中
    with np.printoptions(threshold=np.inf):
        print("0:",vector_array[0])
        print("1:",vector_array[1])
    print("users:",dataset.n_users)
    print("items:",dataset.m_items)

# 恢复原始的 stdout
sys.stdout = original_stdout