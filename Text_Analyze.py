import networkx as nx
import operator
from collections import Counter
from community import community_louvain as lv

# 폰트 설정을 위한 font_manager import
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
# 폰트 설정
#fm._rebuild()# 1회에 한해 실행해준다. (폰트 새로고침, 여러번 해줘도 관계는 없다.)
font_fname = 'C:/Users/user/AppData/Local/Microsoft/Windows/Fonts/SDSamliphopangcheTTFBasic.ttf'      # 여기서 폰트는 C:/Windows/Fonts를 참고해도 좋다.
fontprop = fm.FontProperties(fname=font_fname, size=18).get_name()

def make_edge_list(df):
    """ Edge list 작성 """
    edge_list = []
    for keywords in df['keyword_mecab']:
        #keywords = list(keywords_dict) #위에서 set으로 했으면 추가
        num_keyword = len(keywords)
        if num_keyword > 0:
            for i in range(num_keyword-1):
                for j in range(i+1, num_keyword):
                    edge_list += [tuple(sorted([keywords[i], keywords[j]]))]    # node 간 위해 sorted 사용
    edges = list(Counter(edge_list).items())

    """ networkx Graph 작성 """
    G = nx.Graph((x, y, {'weight': v}) for (x, y), v in edges)
    """ Community 추출 """
    partition = lv.best_partition(G)
    nx.set_node_attributes(G, partition, "community")   # graph G에 community 속성 추가

    """ Gephi file 작성 """
    nx.write_gexf(G, 'data/result/result.gexf')
    return edges

def draw_SNA(edges):
    # 중심성 척도 계산을 위한 Graph를 만든다
    G_centrality = nx.Graph((x, y, {'weight': v}) for (x, y), v in edges)
    # 빈도수가 일정 수 이상인 단어쌍에 대해서만 edge(간선)을 표현한다.
    for ind in range((len(edges))):
        G_centrality.add_edge(edges[ind][0][0], edges[ind][0][1], weight=edges[ind][1])

    dgr = nx.degree_centrality(G_centrality)        # 연결 중심성
    btw = nx.betweenness_centrality(G_centrality)   # 매개 중심성
    cls = nx.closeness_centrality(G_centrality)     # 근접 중심성
    egv = nx.eigenvector_centrality(G_centrality)   # 고유벡터 중심성
    pgr = nx.pagerank(G_centrality)                 # 페이지 랭크

    # 중심성이 큰 순서대로 정렬한다.
    sorted_dgr = sorted(dgr.items(), key=operator.itemgetter(1), reverse=True)
    sorted_btw = sorted(btw.items(), key=operator.itemgetter(1), reverse=True)
    sorted_cls = sorted(cls.items(), key=operator.itemgetter(1), reverse=True)
    sorted_egv = sorted(egv.items(), key=operator.itemgetter(1), reverse=True)
    sorted_pgr = sorted(pgr.items(), key=operator.itemgetter(1), reverse=True)

    # 단어 네트워크를 그려줄 Graph 선언
    G = nx.Graph((x, y, {'weight': v}) for (x, y), v in edges)
    # 페이지 랭크에 따라 두 노드 사이의 연관성을 결정한다. (단어쌍의 연관성)
    # 연결 중심성으로 계산한 척도에 따라 노드의 크기가 결정된다. (단어의 등장 빈도수)
    for i in range(len(sorted_pgr)):
        G.add_node(sorted_pgr[i][0], nodesize=sorted_dgr[i][1])
    for ind in range((len(edges))):
        G.add_weighted_edges_from([(edges[ind][0][0], edges[ind][0][1], edges[ind][1])])
        
    # 노드 크기 조정
    sizes = [G.nodes[node]['nodesize'] * 20000 for node in G]
    options = {
        'edge_color': '#FFDEA2',
        'width': 1,
        'with_labels': True,
        'font_weight': 'regular',
        'alpha' : 0.5
    }

    plt.figure(figsize=(15,15))
    nx.draw(G, node_size=sizes, pos=nx.spring_layout(G, k=3.5, iterations=100), **options, font_family=fontprop)  # font_family로 폰트 등록
    ax = plt.gca()
    ax.collections[0].set_edgecolor("#555555")
    plt.show()


#주요키워드