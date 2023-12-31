import networkx as nx
import operator
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from community import community_louvain as lv
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
from wordcloud import WordCloud

# 폰트 설정을 위한 font_manager import
import matplotlib.font_manager as fm

# 폰트 설정
#fm._rebuild()# 1회에 한해 실행해준다. (폰트 새로고침, 여러번 해줘도 관계는 없다.)
font_fname = 'C:\\Windows\\Fonts\\HMKMRHD.ttf'
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

def draw_SNA(df, edges_, file_name):    
    # 최소 출연 횟수
    if len(df) <= 100:
        min_num = 2
    elif len(df) <= 500:
        min_num = 20
    elif len(df) <= 1000:
        min_num = 30
    else: min_num = 50
    edges = [x for x in edges_ if int(x[1]) >= min_num] #gexf 파일에 적용한 내용은 min_num이 적용되지 않음(make_edge_list 단계에서 저장)
    
    # 중심성 척도 계산을 위한 Graph를 만든다
    G_centrality = nx.Graph((x, y, {'weight': v}) for (x, y), v in edges)
    # 빈도수가 일정 수 이상인 단어쌍에 대해서만 edge(간선)을 표현한다.
    for ind in range((len(edges))):
        G_centrality.add_edge(edges[ind][0][0], edges[ind][0][1], weight=edges[ind][1])

    #dgr = nx.degree_centrality(G_centrality)        # 연결 중심성
    #btw = nx.betweenness_centrality(G_centrality)   # 매개 중심성
    #cls = nx.closeness_centrality(G_centrality)     # 근접 중심성
    #egv = nx.eigenvector_centrality(G_centrality, max_iter=200)   # 고유벡터 중심성
    pgr = nx.pagerank(G_centrality)                 # 페이지 랭크

    # 중심성이 큰 순서대로 정렬한다.
    try: 
        egv = nx.eigenvector_centrality(G_centrality, max_iter=200)   # 고유벡터 중심성
        sorted_egv = sorted(egv.items(), key=operator.itemgetter(1), reverse=True)
        param = sorted_egv
    except: # 고유벡터 중심성 생성 오류가 발생할 경우 연결 중심성으로
        dgr = nx.degree_centrality(G_centrality)        # 연결 중심성
        sorted_dgr = sorted(dgr.items(), key=operator.itemgetter(1), reverse=True)
        param = sorted_dgr
    #btw = nx.betweenness_centrality(G_centrality)   # 매개 중심성
    #sorted_btw = sorted(btw.items(), key=operator.itemgetter(1), reverse=True)
    #cls = nx.closeness_centrality(G_centrality)     # 근접 중심성
    #sorted_cls = sorted(cls.items(), key=operator.itemgetter(1), reverse=True)
    
    sorted_pgr = sorted(pgr.items(), key=operator.itemgetter(1), reverse=True)

    # 단어 네트워크를 그려줄 Graph 선언
    G = nx.Graph((x, y, {'weight': v}) for (x, y), v in edges)
    # 페이지 랭크에 따라 두 노드 사이의 연관성을 결정한다. (단어쌍의 연관성)
    # 연결 중심성으로 계산한 척도에 따라 노드의 크기가 결정된다. (단어의 등장 빈도수)
    for i in range(len(sorted_pgr)):
        G.add_node(sorted_pgr[i][0], nodesize=param[i][1])
    for ind in range((len(edges))):
        G.add_weighted_edges_from([(edges[ind][0][0], edges[ind][0][1], edges[ind][1])])
        
    # 노드 크기 조정
    sizes = [G.nodes[node]['nodesize'] * 20000 for node in G]
    options = {
        'edge_color': '#FFDEA2',
        'width': 1,
        'with_labels': True,
        'font_weight': 'regular',
        'alpha' : 0.5 #투명도
    }

    plt.figure(figsize=(15,15))
    nx.draw(G, node_size=sizes, pos=nx.spring_layout(G, k=3.5, iterations=200), **options, font_family=fontprop)  # font_family로 폰트 등록
    #ax = plt.gca()
    #ax.collections[0].set_edgecolor("#555555")
    plt.savefig(f"data/visualization/SNA_{file_name}.png")
    plt.close('all')


# 동시출연빈도(클래스)
class Documents:
    def __init__(self, path):
        self.path = path
    def __iter__(self):
        with open(self.path, encoding='utf-8') as f:
            for doc in f:
                yield doc.strip().split()
# 동시출연빈도(함수)
def make_corpus(df):
    # 파일로 저장
    with open('data/result/corpus.txt','w',encoding='UTF-8') as f:
        for i in df['keyword_mecab']: #이미 전처리가 된 파일을 가져왔기때문에 추가적인 전처리 작업 없이 진행
            f.write(' '.join(s for s in i)+'\n')

    corpus_path = 'data/result/corpus.txt'
    documents = Documents(corpus_path)
    word_counter = Counter((word for words in documents for word in words))
    return word_counter

#워드클라우드(빈도기반)
def draw_word_cloud(word_counter, file_name):
    noun_list = word_counter.most_common(100)
    font_path = font_fname
    wc = WordCloud(font_path=font_path,
            background_color="white",
            #mask = mask,
            width=1000,
            height=1000, 
            max_words=100,
            max_font_size=300)
    wc.generate_from_frequencies(dict(noun_list))
    plt.figure(figsize=(10,10))
    plt.axis('off')
    plt.imshow(wc.generate_from_frequencies(dict(noun_list)))
    plt.savefig(f"data/visualization/word_cloud_{file_name}.png")
    plt.close('all')

#주요키워드(결과값이 빈도와 거의 비슷하지만 조금 다름)
def tfidf(df, file_name):
    corpus = []
    with open('data/result/corpus.txt', 'r', encoding='utf-8') as f:
        for doc in f:
            corpus.append(doc.strip())

    tfidfv = TfidfVectorizer().fit(corpus)
    #vectorizer = TfidfVectorizer()
    #sp_matrix = vectorizer.fit_transform(corpus)

    word2id = defaultdict(lambda : 0)
    for idx, feature in enumerate(tfidfv.get_feature_names_out()):
        word2id[feature] = idx
    tfidf = TfidfVectorizer(max_features=500, stop_words='english')
    tdm = tfidf.fit_transform(df['keyword_mecab'].apply(lambda x: ' '.join(x)))
    word_count = pd.DataFrame({
        '단어': tfidf.get_feature_names_out(),
        '빈도': tdm.sum(axis=0).flat
    })
    word_count.sort_values('빈도', ascending=False).head(50).to_csv(f"data/visualization/tiidf_{file_name}.csv", index=False, encoding='cp949')
    #return word_count.sort_values('빈도', ascending=False).head(50)#.reset_index().drop(['index'],axis=1)
