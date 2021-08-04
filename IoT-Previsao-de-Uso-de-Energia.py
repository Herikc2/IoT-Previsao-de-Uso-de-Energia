#!/usr/bin/env python
# coding: utf-8

# # 1. Problema de Negócio

# O conjunto de dados foi coletado por um 
# período de 10 minutos por cerca de 5 meses. As condições de temperatura e 
# umidade da casa foram monitoradas com uma rede de sensores sem fio ZigBee. 
# Cada nó sem fio transmitia as condições de temperatura e umidade em torno 
# de 3 min. Em seguida, a média dos dados foi calculada para períodos de 10 minutos. 
# 
# Os dados de energia foram registrados a cada 10 minutos com medidores de 
# energia de barramento m. O tempo da estação meteorológica mais próxima do 
# aeroporto (Aeroporto de Chievres, Bélgica) foi baixado de um conjunto de dados 
# públicos do Reliable Prognosis (rp5.ru) e mesclado com os conjuntos de dados 
# experimentais usando a coluna de data e hora. Duas variáveis aleatórias foram 
# incluídas no conjunto de dados para testar os modelos de regressão e filtrar os 
# atributos não preditivos (parâmetros).
# 
# O nosso objetivo é prever o uso de energia armazenado na variavel 'Appliances', dessa forma iremos construir um modelo de Regressão.
# 
# -- Objetivos
# - R^2 superior a 70%
# - RMSE inferior a 20
# - MAE inferior a 15
# - Acuracia superior a 80%
# - Relatar economia total de energia.

# | Feature     | Descrição                                          | Unidade        |
# |-------------|----------------------------------------------------|----------------|
# | date        | Data no formato ano-mês-dia hora:minutos:segundos. |                |
# | Appliances  | Consumo de energia. Variavel Target.               | Wh (Watt-Hora) |
# | lights      | Consumo de energia de luminárias.                  | Wh (Watt-Hora) |
# | T1          | Temperatura na Cozinha.                            | Celsius        |
# | RH1         | Umidade Relativa na Cozinha.                       | %              |
# | T2          | Temperatura na Sala de Estar.                      | Celsius        |
# | RH2         | Umidade Relativa na Sala de Estar.                 | %              |
# | T3          | Temperatura na Lavanderia.                         | Celsius        |
# | RH3         | Umidade Relativa na Lavanderia.                    | %              |
# | T4          | Temperatura no Escritório.                         | Celsius        |
# | RH4         | Umidade Relativa no Escritório.                    | %              |
# | T5          | Temperatura no Banheiro.                           | Celsius        |
# | RH5         | Umidade Relativa no Banheiro.                      | %              |
# | T6          | Temperatura Externa Lado Norte.                    | Celsius        |
# | RH6         | Umidade Relativa Externa Lado Norte.               | %              |
# | T7          | Temperatura na Sala de Passar Roupa.               | Celsius        |
# | RH7         | Umidade Relativa na Sala de Passar Roupa.          | %              |
# | T8          | Temperatura no Quarto do Adolescente.              | Celsius        |
# | RH8         | Umidade Relativa no Quarto do Adolescente.         | %              |
# | T9          | Temperatura no Quarto dos Pais.                    | Celsius        |
# | RH9         | Umidade Relativa no Quarto dos Pais.               | %              |
# | T_out       | Temperatura Externa.                               | Celsius        |
# | Press_mm_hg | Pressão.                                           | mm/hg          |
# | RH_out      | Umidade Relativa Externa.                          | %              |
# | Windspeed   | Velocidade do Vento.                               | m/s            |
# | Visibility  | Visibilidade.                                      | km             |
# | Tdewpoint   | Ponto de Saturação.                                | Celsius        |
# | rv1         | Variável Randômica.                                |                |
# | rv2         | Variável Randômica.                                |                |
# | NSM         | Segundos até a meioa noite                         |                |
# | WeekStatus  | Indicativo de Dia da Semana ou Final de Semana.    |                |
# | Day_of_week | Indicativo de Segunda à Domingo.                   |                |

# # 2. Imports

# In[1]:


get_ipython().system('pip install ipywidgets -q')


# In[2]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import sweetviz as sv
import statsmodels.api as sm
import statsmodels.formula.api as smf
import shap

from warnings import simplefilter
from matplotlib.colors import ListedColormap
from math import ceil
from statsmodels.graphics.gofplots import qqplot
from scipy.stats import normaltest, kurtosis
from statsmodels.stats.outliers_influence import variance_inflation_factor
from smogn import smoter
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from holidays import Belgium
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import SelectFromModel
from sklearn.linear_model import LinearRegression, Ridge, LassoCV
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split, RandomizedSearchCV, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.svm import SVR, LinearSVR
from sklearn.feature_selection import RFE
from catboost import CatBoostRegressor


# In[3]:


# Versões dos pacotes usados neste jupyter notebook
get_ipython().run_line_magic('reload_ext', 'watermark')
get_ipython().run_line_magic('watermark', '-a "Herikc Brecher" --iversions')


# ## 2.1 Ambiente

# In[4]:


simplefilter(action='ignore', category=FutureWarning)
get_ipython().run_line_magic('matplotlib', 'inline')
sns.set_theme()


# In[5]:


seed_ = 194
np.random.seed(seed_)


# # 3. Carregamento dos Dados

# In[6]:


# Carregamento do dataset de treino e teste
dtTreino = pd.read_csv('data/training.csv')
dtTeste = pd.read_csv('data/testing.csv')


# In[7]:


dtTreino.head()


# In[8]:


dtTeste.head()


# In[9]:


dtFull = pd.concat([dtTreino, dtTeste], axis = 0)


# In[10]:


dtFull.head()


# In[11]:


print(dtTreino.shape, dtTeste.shape, dtFull.shape)


# # 4. Analise Exploratoria

# In[12]:


dtFull.head()


# Possuimos ao todo 19375 observações, unindo o conjunto de treino e teste.

# In[13]:


dtFull.describe()


# A unica feature que aparenta estar no formato errado é a coluna 'Date', essa que é 'datetime' foi carregada como 'object'.

# In[14]:


dtFull.dtypes


# In[15]:


# Copiando para um dataset onde iremos processar os dados
dtProcessado = dtFull.copy()

# Convertendo a coluna 'date' para 'datetime'
dtProcessado['date'] = pd.to_datetime(dtProcessado['date'], format='%Y-%m-%d %H:%M:%S')


# In[16]:


dtProcessado.dtypes


# Agora os dados estão no formato correto, e não tivemos perda de informação.

# In[17]:


dtProcessado.head()


# In[18]:


# Verificando se possui valor missing/NA
print(dtProcessado.isna().sum())


# Colunas como 'date', 'rv1' e 'rv2' possuem valores unicos para cada observação, sendo 1:1. Iremos verificar depois se essas informações são relevantes para o modelo, pois isso pode causar problemas.

# In[19]:


# Verificando valores unicos
print(dtProcessado.nunique())


# In[20]:


# Verificando se possui valores duplicados
print(sum(dtProcessado.duplicated()))


# Para melhor interpretação dos dados, iremos separa eles em variaveis qualitativas e quantitativas.

# In[21]:


qualitativas = ['WeekStatus', 'Day_of_week']
quantitativas = dtProcessado.drop(['WeekStatus', 'Day_of_week', 'date'], axis = 1).columns


# In[22]:


dtProcessado[qualitativas].head()


# In[23]:


dtProcessado[quantitativas].head()


# # 4.2 Geração de plots e insights

# Analisando o grafico abaixo é perceptivel que o consumo de energia nos 'Weekend' são proporcionais aos 'Weekday'. Já que a 'Weekday' representa exatatemente 28.5% de uma semana. Por acaso esse também é o valor do consumo de energia em %.

# In[24]:


# Consumo de energia entre dias da semana e finais de semana
plt.pie(dtProcessado.groupby('WeekStatus').sum()['Appliances'], labels = ['Weekday', 'Weekend'], autopct = '%1.1f%%')
plt.show()


# É perceptivel que ao longo do periodo da coleta dos dados mantemos oscilações comuns no consumo de energia, provavel que se de por eventos climaticos ao longo do periodo.

# In[25]:


plt.plot(dtProcessado['date'], dtProcessado['Appliances'])


# In[26]:


def scatter_plot_conjunto(data, columns, target):
    # Definindo range de Y
    y_range = [data[target].min(), data[target].max()]
    
    for column in columns:
        if target != column:
            # Definindo range de X
            x_range = [data[column].min(), data[column].max()]
            
            # Scatter plot de X e Y
            scatter_plot = data.plot(kind = 'scatter', x = column, y = target, xlim = x_range, ylim = y_range,                                    c = ['black'])
            
            # Traçar linha da media de X e Y
            meanX = scatter_plot.plot(x_range, [data[target].mean(), data[target].mean()], '--', color = 'red', linewidth = 1)
            meanY = scatter_plot.plot([data[column].mean(), data[column].mean()], y_range, '--', color = 'red', linewidth = 1)


# É perceptivel que as variaveis 'T*' como 'T1', 'T2'... possuem baixa correlação com a variavel target. Onde possuimos concentrações maiores para valores médios, porém ao aumentarem ou diminuirem muito passam a diminuir a 'Appliances'. Já variaveis 'RH_*' possuem uma correlação um pouco maior.

# In[27]:


scatter_plot_conjunto(dtProcessado, quantitativas, 'Appliances')


# ## 4.3 Distribuição dos Dados

# Iremos verificar se os nossos dados possuem uma distribuição Gaussiana ou não. Dessa forma iremos entender quais metodos estatisticos utilizar. Distribuições Gaussianas utilizam de métodos estatisticos paramétricos. Já o contrário utiliza de métodos estatisticos não paramétricos. É importante entender qual método utilizar para não termos uma vissão errada sobre os dados.

# In[28]:


def quantil_quantil_teste(data, columns):
    
    for col in columns:
        print(col)
        qqplot(data[col], line = 's')
        plt.show()


# Olhando os graficos abaixo, possuimos algumas variaveis que não seguem a reta Gaussiana, indicando dados não normalizados, porém para termos certeza, iremos trazer isso para uma representação numerica, onde podemos ter uma maior certeza.

# In[29]:


quantil_quantil_teste(dtProcessado, quantitativas)


# In[30]:


def testes_gaussianos(data, columns, teste):
    
    for i, col in enumerate(columns):
        print('Teste para a variavel', col)
        alpha = 0.05
        
        if teste == 'shapiro':
            stat, p = shapiro(data[col])
        elif teste == 'normal':
            stat, p = normaltest(data[col])           
        elif teste == 'anderson':
            resultado = anderson(data[col])
            print('Stats: %.4f' % resultado.statistic)
            
            for j in range(len(resultado.critical_values)):
                sl, cv = resultado.significance_level[j], resultado.critical_values[j]
                
                if resultado.statistic < cv:
                    print('Significancia = %.4f, Valor Critico = %.4f, os dados parecem Gaussianos. Falha ao rejeitar H0.' % (sl, cv))
                else:
                    print('Significancia = %.4f, Valor Critico = %.4f, os dados não parecem Gaussianos. H0 rejeitado.' % (sl, cv))
            
        if teste != 'anderson':         
            print('Stat = ', round(stat, 4))
            print('p-value = ', round(p, 4))
            #print('Stats = %4.f, p = %4.f' % (stat, p))

            if p > alpha:
                print('Os dados parecem Gaussianos. Falha ao rejeitar H0.')
            else:
                print('Os dados não parecem Gaussianos. H0 rejeitado.')
            
        print('\n')


# # 4.3.1 Teste normal de D'Agostino

# O teste Normal de D'Agostino avalia se os dados são Gaussianos utilizando estatisticas resumidas como: Curtose e Skew.

# Aparentemente os nossos dados não seguem o comportamento Gaussiano, dessa forma iremos ter que tomar medidas estatisticas para amenizar o impacto na hora da modelagem preditiva.

# In[31]:


testes_gaussianos(dtProcessado, quantitativas, teste = 'normal')


# Analisando abaixo o boxplot das variaveis quantitativas, percebemos que algumas variaveis possuem muitos outliers e irão necessitar um tratamento.
# 
# Sendo alguas delas: 'Appliances', 'T1', 'RH_1', 'Visibility', 'RH_5'. Sendo alguns outliers somente para valores maximos e outros para valores minimos.

# In[32]:


# Plot para variaveis quantitativas

fig = plt.figure(figsize = (16, 32))

for i, col in enumerate(quantitativas):
    plt.subplot(10, 3, i + 1)
    dtProcessado.boxplot(col)
    plt.tight_layout()


# Visualizando rapidamente o heatmap, percebemos que existem valores muito proximo de preto e outros muito proximo de branco, valores esses fora da diagonal principal, indicando fortes indicios de multicolinearidade, o que para modelos de regressão são prejudiciais. 
# 
# Um segundo ponto são as variaveis 'rv1' e 'rv2' que possuem correlação 1, de acordo com o nosso dicionario de dados essas variaveis são randomicas, então irão ser removidas do dataset de qualquer maneira. Já o NSM é uma variavel sequencial, que também irá ser removida.

# In[33]:


fig = plt.figure(figsize = (32, 32))

sns.heatmap(dtProcessado[quantitativas].corr(method = 'pearson'), annot = True, square = True)
plt.show()


# Apartir do Sweetviz confirmamos que possuimos muitas variaveis com alta correlação, o que irá gerar Multicolinearidade, para tentarmos amenizar o impacto iremos utilizar de autovetores. 
# 
# Observação: O report foi analisado e anotado insights, porém para melhor compreensão passo a passo dos dados, iremos realizar a analise de forma manual ao longo do notebook.

# In[34]:


# Gerando relatorio de analise do Sweetviz
#relatorio = sv.analyze(dtProcessado)
#relatorio.show_html('docs/eda_report.html')


# In[35]:


# Remoção de variaveis desnecessárias a primeira vista

dtProcessado = dtProcessado.drop(['rv1', 'rv2'], axis = 1)
quantitativas = quantitativas.drop(['rv1', 'rv2'])


# # 4.4 Avaliando MultiColinearidade

# In[36]:


dtProcessado_Temp = dtProcessado.copy()
dtProcessado_Temp = dtProcessado_Temp.drop(['date', 'Appliances'], axis = 1)

# Capturando variaveis independentes e dependentes
X = dtProcessado_Temp[quantitativas.drop('Appliances')]

# Gerando matriz de correlação e recombinando
corr = np.corrcoef(X, rowvar = 0)
eigenvalues, eigenvectors = np.linalg.eig(corr)


# In[37]:


menor = 999
index = 0
for i, val in enumerate(eigenvalues):
    if val < menor:
        menor = val
        index = i


# In[38]:


print('Menor valor do eigenvalues:', menor, 'Index:', index)


# In[39]:


menorEigenVector = abs(eigenvectors[:, 19])


# In[40]:


for i, val in enumerate(eigenvectors[:, 19]):
    print('Variavel', i,':', abs(val))


# In[41]:


colunas = dtProcessado_Temp.columns


# Analisando as variaveis de indice 11, 19, 21 e 24, aparentam possuir multicolinearidade devido ao seu alto valor absoluto. Porém a sua correlação é baixa, dessa forma iremos aprofundar mais a analise para tomarmos alguma decisão.

# In[42]:


colunas[[11, 19, 21, 24]]


# A variavel 'RH_5' não apresenta um comportamento nitido de correlação com as demais variaveis no scatter_plot. Porém, apresenta uma tendencia pequena de aumento nos valores de 'RH_5' apartir de uma determinada crescente nas variaveis independentes.

# In[43]:


scatter_plot_conjunto(dtProcessado_Temp, ['RH_5', 'RH_9', 'Press_mm_hg', 'Visibility'], 'RH_5')


# Para 'RH_9' temos o mesmo detalhe, não apresenta um comportamento nitido de correlação com as demais variaveis no scatter_plot. Porém, apresenta uma tendencia pequena de aumento nos valores de 'RH_9' apartir de uma determinada crescente nas variaveis independentes. 

# In[44]:


scatter_plot_conjunto(dtProcessado_Temp, ['RH_5', 'RH_9', 'Press_mm_hg', 'Visibility'], 'RH_9')


# Para 'RH_9' temos o mesmo detalhe, não apresenta um comportamento nitido de correlação com as demais variaveis no scatter_plot.

# In[45]:


scatter_plot_conjunto(dtProcessado_Temp, ['RH_5', 'RH_9', 'Press_mm_hg', 'Visibility'], 'Press_mm_hg')


# Para 'Visibility' temos o mesmo detalhe, não apresenta um comportamento nitido de correlação com as demais variaveis no scatter_plot. Porém, apresenta uma tendencia pequena de aumento nos valores de 'Visibility' apartir de uma determinada crescente nas variaveis independentes.

# In[46]:


scatter_plot_conjunto(dtProcessado_Temp, ['RH_5', 'RH_9', 'Press_mm_hg', 'Visibility'], 'Visibility')


# Analisando as variaveis que apontam possuir alguma Multicolinearidade, até o momento não conseguimos identificar com alta confiança se isso se é verdade. Iremos utilizar VIF para verificar o impacto das variaveis de maneira mais automatizada e acertiva. 
# 
# É esperado que valores de VIF = 1 ou proximos a 1 não possua correlação com outras variaveis independentes. Caso VIF ultrapasse valores como 5 ou até 10, possuimos fortes indicios de multicolinearidade entre as variaveis com tal valor.

# In[47]:


def calcular_VIF(X):
    vif = pd.DataFrame()
    vif['Features'] = X.columns
    vif['VIF'] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    
    return vif


# In[48]:


dtProcessado_Temp = dtProcessado.copy()
dtProcessado_Temp = dtProcessado_Temp.drop(['Appliances'], axis = 1)

# Capturando variaveis independentes
X = dtProcessado_Temp[quantitativas.drop('Appliances')]


# Analisando abaixo é perceptivel que a unica variavel com valor baixo para VIF é 'lights'. Assim iremos necessitar de um grande tratamento sobre as variaveis.

# In[49]:


calcular_VIF(X)


# Abaixo realizamos a primeira tentativa removendo variaveis com VIF > 2000. Porém ainda possuimos alto indice de MultiColinearidade. Iremos remover variaveis com VIF > 1000.

# In[50]:


X_temp = X.drop(['T1', 'T2', 'T9', 'Press_mm_hg'], axis = 1)
calcular_VIF(X_temp)


# Ainda com a remoção de VIF > 1000 estamos com fortes indicios de MultiColinearidade, iremos aumentar o nosso range para VIF > 250.

# In[51]:


X_temp = X.drop(['T1', 'T2', 'T9', 'Press_mm_hg', 'RH_1', 'RH_3', 'RH_4', 'T7'], axis = 1)
calcular_VIF(X_temp)


# Após uma remoção massiva de variaveis continuamos com alta taxa de MultiColinearidade, iremos remover mais algumas variaveis. Porém, é esperado que iremos fazer mais testews nas variaveis para verificar seu valor para a predição.

# In[52]:


X_temp = X.drop(['T1', 'T2', 'T9', 'Press_mm_hg', 'RH_1', 'RH_3', 'RH_4', 'T7', 'T3', 'T4', 'T5', 'T8', 'RH_9', 'RH_2',                'RH_7', 'RH_8'], axis = 1)
calcular_VIF(X_temp)


# Após removermos 21 variaveis das 25 variaveis quantitativas, conseguimos reduzir o VIF para um valor aceitavel, porém é necessário verificar o impacto dessa remoção e se a tecnica para sua remoção foi utilizada da maneira correta.

# In[53]:


X_temp = X.drop(['T1', 'T2', 'T9', 'Press_mm_hg', 'RH_1', 'RH_3', 'RH_4', 'T7', 'T3', 'T4', 'T5', 'T8', 'RH_9', 'RH_2',                'RH_7', 'RH_8', 'RH_5', 'T_out', 'Visibility', 'RH_out', 'T6'], axis = 1)
calcular_VIF(X_temp)


# Iremos verificar o valor das variaveis utilizando tanto o dataset original quanto com as variaveis removidas apartir do calculo de VIF. Para isso iremos utilizar um modelo base de regressão lienar do StatsModels.

# In[54]:


# Carregando todas variaveis com exceção da 'Target', iremos adicionar a constante exigida pelo modelo
X = dtProcessado_Temp.copy().drop('date', axis = 1)[quantitativas.drop('Appliances')]
Xc = sm.add_constant(X)

y = dtProcessado['Appliances'].values


# In[55]:


# Criando e treinando modelo
modelo = sm.OLS(y, Xc)
modelo_v1 = modelo.fit()


# Analisando abaixo percemos que o nosso modelo representa somente 16.5% da variancia dos dados, R-squared. Também verificamos que o valor F esta muito alto, sendo inviavel utilizar pare predição. Nosso AIC e BIC já indicam um valor muito alto, o que esta nos sinalizando MultiColinearidade.
# 
# Também possuimos variaveis como 'T1', 'RH_4', 'T5', 'RH_5', 'T7' e 'Press_mm_hg' com valores de p > 0.05, indicando que não possui relação com a predição de variaveis. 
# 
# Possuimos um 'Omnibus' muito alto, visto que o ideal seria 0. Já Skew e Kurtosis possuem valores relativamente normais para dos que não foram tratados. Já o Durbin-Watson está com um valor relativamente proximo do normal (entre 1 e 2), porém esta indicando que os nossos dados podem estar concentrados, a medida que o ponto de dados aumenta o erro relativo aumenta. Por ultimo, estamos com um 'Conditiom Number' extremamente alto, indicando mais ainda a nossa multicolienaridade.

# In[56]:


# Visualizando resumo do modelo
modelo_v1.summary()


# Abaixo iremos criar o modelo novamente porém a redução de variaveis implicadas pelo p value e VIF.

# In[57]:


# Carregando variaveis com exceção
Xc = sm.add_constant(X_temp)

y = dtProcessado['Appliances'].values


# In[58]:


# Criando e treinando modelo
modelo = sm.OLS(y, Xc)
modelo_v2 = modelo.fit()


# Treinando o modelo com a remoção de variaveis, notamos que tivemos uma grande redução no R-Squared, trazendo uma significancia de apenas 6% da variancia dos nossos dados. Devemos tentar escolher variaveis melhores para o nosso modelo, consequentemente levou ao aumento do valor F e diminuição do 'Log-Likelihood'.
# 
# Outros valores permaneceram com resultados semelhantes, com exceção de 'Conditiom Number' que reduziu drasticamente ao ponto de não sofrermos mais multicolinearidade.
# 
# Iremos ter que avaliar melhor quais variaveis utilizar para o nosso modelo, afim de reduzir a MultiColinearidade sem perder variaveis de valor.

# In[59]:


# Visualizando resumo do modelo
modelo_v2.summary()


# ## 4.5 Simetria dos Dados

# ### 4.5.1 Skewness

# Esperamos valores de Skewness proximo de 0 para uma simetria perfeita.
# 
# ![image.png](attachment:image.png)

# - Se skewness é menor que −1 ou maior que +1, a distribuição é 'highly skewed'.
# 
# - Se skewness esta entre −1 e −½ ou entre +½ e +1, a distribuição é 'moderately skewed'.
# 
# - Se skewness esta entre −½ e +½, a distribuição é aproximadaente simetrica.

# Olhando primeiramente para o Skewness, possuimos variaveis com alta simetria o que é muito bom para os algoritmos de Machine Learnign em geral. Porém possuimo a variavel 'lights' com um simetria muito acima de 0. Já as outras variaveis possuem um Skewness aceitavel, valores maiores que 0.5 ou menores que -0.5 indicam que a simetria já começa a se perder, porém ainda é aceitavel.

# In[60]:


print(dtProcessado[quantitativas].skew(), '\nSoma:', sum(abs(dtProcessado[quantitativas].skew())))


# ### 4.5.2 Histograma

# In[61]:


def hist_individual(data, columns, width = 10, height = 15):
    fig = plt.figure()
    fig.subplots_adjust(hspace = 0.4, wspace = 0.4)
    fig.set_figheight(10)
    fig.set_figwidth(15)
    
    columns_adjust = ceil(len(columns) / 3)
    
    for i, column in enumerate(columns):
        ax = fig.add_subplot(columns_adjust, 3, i + 1)
        data[column].hist(label = column)
        plt.title(column)
        
    plt.tight_layout()  
    plt.show()


# Abaixo iremos verificar o histograma das variaveis. Porém para visualizarmos de uma melhor forma iremos separar em grupos de plots abaixo. Fica perceptivel que 'Appliances' e'lights' não possuem simetria, devido a sua alta concentração entre 0 e 10. Porém variaveis como 'T1' e 'T4' possuem alta simetria.

# In[62]:


hist_individual(dtProcessado, quantitativas[0:9])


# In[63]:


hist_individual(dtProcessado, quantitativas[9:18])


# In[64]:


hist_individual(dtProcessado, quantitativas[18:27])


# ### 4.5.3 Exceço de Kurtosis

# ![image.png](attachment:image.png)

# Mesokurtic -> Kurtosis ~= 0: Distribuição normal.
# 
# Leptokurtic -> Kurtosis > 0: Valores proximos a media ou dos extremos.
# 
# Platykurtic -> Kurtosis < 0: Valores muito espalhados.

# É perceptivel que variaveis como 'Appliances', 'lights' e 'RH_5' claramente estão distantes de uma distribuição normal, porém outras variaveis se aproximam de uma distribuição Gaussiana, com valores maiores que 3 e menores que 4. Também é perceptivel qque possuimos muitas variaveis com o comportamento de uma 'Platykurtic', ou seja valores muito espalhados. 

# In[65]:


print(dtProcessado[quantitativas].kurtosis(), '\nSoma:', sum(abs(dtProcessado[quantitativas].kurtosis())))


# ## 4.6 Analise Temporal

# ### 4.6.1 Pre-Processamento colunas temporais

# Para realizarmos uma analise eficiente das variaveis temporais, iremos transforma-las, adicionando coluna de 'Month', 'Day', 'Hour', e convertendo coluna 'Day_of_week' e 'WeekStatus' para numericas.

# In[66]:


# Renomeando coluna WeekStatus para Weekend
dtProcessado = dtProcessado.rename(columns = {'WeekStatus': 'Weekend'})


# In[67]:


# Dia de semana = 0, final de semana = 1
dtProcessado['Day_of_week'] = dtProcessado['date'].dt.dayofweek
dtProcessado['Weekend'] = 0

dtProcessado.loc[(dtProcessado['Day_of_week'] == 5) | (dtProcessado['Day_of_week'] == 6), 'Weekend'] = 1


# In[68]:


# Criando colunan de Mês, Dia e Hora
dtProcessado['Month'] = dtProcessado['date'].dt.month
dtProcessado['Day'] = dtProcessado['date'].dt.day
dtProcessado['Hour'] = dtProcessado['date'].dt.hour


# In[69]:


dtProcessado.head()


# ### 4.6.2 Analise Temporal de Gasto Energia

# Abaixo percebemos que o gasto energetico por dia da semana tende a iniciar alto na Segunda / 0 em 115 Wh, passando por um queda para 80-85 Wh até Quinta, voltando a subir até os 105 Wh na Sexta e Sabado. Por ultimo, voltamos a uma queda por volta dos 85 Wh no Domingo.
# 
# Apartir desse cenario, podemos visualizar que a Segunda passa a ser um dia onde as pessoas gastam maior energia, talvez por estar começando a semana com maior foco em atividades que leval a gasto de energia eletrica. Com uma queda ao longo da semana, que volta a subir proximo ao final de semana, onde temos dias de descanso que passam a acontecer em casa, e por ultimo no domingo onde tende a ser dias para saida de familia.
# 
# Claro que o cenario acima é somente uma hipotese, porém representar a realidade de algumas pessoas, para um melhor entendimento poderia ser feito uma pesquisa do estilo de vida do cidadões de onde foi retirado o dataset.

# In[70]:


fig, ax = plt.subplots(figsize = (10, 5))
dtProcessado.groupby('Day_of_week').mean()['Appliances'].plot(kind = 'bar')

ax.set_title('Média de Watt-Hora por Dia')
ax.set_ylabel('Watt-Hora')
ax.set_xlabel('Dia da Semana')
plt.plot()


# In[71]:


fig, ax = plt.subplots(figsize = (10, 5))
dtProcessado.groupby('Day_of_week').sum()['Appliances'].plot(kind = 'bar')

ax.set_title('Soma de Watt-Hora por Dia')
ax.set_ylabel('Watt-Hora')
ax.set_xlabel('Dia da Semana')
plt.plot()


# É analisado que o gasto de hora começa a subir aproximadamente as 6 da manhã até as 11 horas da manhã chegar em um pico de 130 Wh, depois temos uma queda até os 100 Wh e voltamos a subir pro volta das 15 horas da tarde, até chegar ao pico de 180 Wh as 18 horas, apartir desse momento vamos caindo o nivel de energia até chegar abaixo dos 60 Wh as 23 horas.

# In[72]:


fig, ax = plt.subplots(figsize = (10, 5))
dtProcessado.groupby('Hour').mean()['Appliances'].plot(kind = 'line')

ax.set_title('Media de Watt-Hora por Hora')
ax.set_ylabel('Watt-Hora')
ax.set_xlabel('Hora do Dia')
plt.plot()


# In[73]:


fig, ax = plt.subplots(figsize = (10, 5))
dtProcessado.groupby('Hour').sum()['Appliances'].plot(kind = 'line')

ax.set_title('Soma de Watt-Hora por Hora')
ax.set_ylabel('Watt-Hora')
ax.set_xlabel('Hora do Dia')
plt.plot()


# In[74]:


# Criando copia do data set
dtProcessado_temporal = dtProcessado.copy()

# Set da data como index
dtProcessado_temporal.index = dtProcessado_temporal['date']
dtProcessado_temporal = dtProcessado_temporal.drop('date', axis = 1)


# In[75]:


dtProcessado_temporal.head()


# In[76]:


# Calculando media por data
dtProcessado_Dia = dtProcessado_temporal['Appliances'].resample('D').mean()

# Calculando media até a data atual
media_momentanea = pd.Series(                        [np.mean(dtProcessado_Dia[:x]) for x in range(len(dtProcessado_Dia))]                        )

media_momentanea.index = dtProcessado_Dia.index


# Percebe-se que o gasto de energia vem oscilando bastante entre os meses, porém mantem uma média constante devido ao alto volume de dados. Talvez a coluna 'Mês' e 'Dia' possuam uma representatividade interessante para o modelo.

# In[77]:


fig, ax = plt.subplots(figsize = (15, 5))
plt.plot(dtProcessado_Dia, label = 'Gasto Energetico Diario')
plt.plot(media_momentanea, label = 'Media de Gasto Energetico')
plt.legend()
plt.xticks(rotation = 90)

ax.set_title('Gasto Médio de Energia Diário em Watt-Hora');


# # 5. Pre-Processamento

# ## 5.1 Removendo Colunas Desnecessárias

# Abaixo iremos remover as colunas que mostraram se sem valor durante a analise exploratoria.

# In[78]:


dtProcessado = dtProcessado.drop(['date'], axis = 1)


# In[79]:


dtProcessado.head()


# ## 5.2 Detectando Outliers

# In[80]:


def boxplot_individuais(data, columns, width = 15, height = 8):
    fig = plt.figure()
    fig.subplots_adjust(hspace = 0.4, wspace = 0.4)
    fig.set_figheight(8)
    fig.set_figwidth(15)
    
    columns_adjust = ceil(len(columns) / 3)
    
    for i, column in enumerate(columns):
        ax = fig.add_subplot(columns_adjust, 3, i + 1)
        sns.boxplot(x = data[column])
        
    plt.tight_layout()  
    plt.show()


# ![image.png](attachment:image.png)

# É perceptivel que com exceção das variaveis: 'RH_4', 'RH_6', 'T7' e 'T9', todas as outras variaveis possuem outliers. Alguns possuem somentne acima do limite inferior, outras apenas do limite superior. Ainda poussimos os casos de variaveis que possuem em ambos os limites.
# 
# Para tratar os outliers iremos utilizar a tecnnica de IQR, iremos mover os dados abaixo do limite inferior para o limite inferior, já para o limite superior iremos mover os dados acima do mesmo para o limite superior.

# In[81]:


boxplot_individuais(dtProcessado, quantitativas[0:9])


# In[82]:


boxplot_individuais(dtProcessado, quantitativas[9:18])


# In[83]:


boxplot_individuais(dtProcessado, quantitativas[18:27])


# ## 5.3 Tratando Outliers

# In[84]:


def calcular_limites_IQR(column):
    # Calcular Q1 e Q3 do array
    Q1 = column.quantile(0.25)
    Q3 = column.quantile(0.75)
    IQR = Q3 - Q1
    limite_inferior = Q1 - 1.5 * IQR
    limite_superior = Q3 + 1.5 * IQR
    
    return limite_inferior, limite_superior

def aplicar_IQR_coluna(column, superior, inferior):
    limite_inferior, limite_superior = calcular_limites_IQR(column)
    
    if inferior:
        column = [limite_inferior if x < limite_inferior else x for x in column]
        
    if superior:      
        column = [limite_superior if x > limite_superior else x for x in column]
    
    return column

def aplicar_IQR(data, columns = [], superior = True, inferior = True):
    
    if len(columns) == 0:
        especificar = False
    else:
        especificar = True
    
    for i, column in enumerate(data.columns):
        if especificar:
            if column in columns:
                data[column] = aplicar_IQR_coluna(data[column], superior, inferior)
        else:
            data[column] = aplicar_IQR_coluna(data[column], superior, inferior)
            
    return data


# Dataset antes da aplicação do IQR para correção de outliers.

# In[85]:


dtProcessado.describe()


# In[86]:


dtProcessado_IQR = dtProcessado.copy()
dtProcessado_IQR = aplicar_IQR(dtProcessado_IQR, columns = dtProcessado_IQR.columns.copy().drop(['lights',                                                                    'Weekend', 'Day_of_week', 'Month', 'Day', 'Hour']))


# Dataset após aplicação do IQR para correção de outliers. Percebe-se que valores minimos e maximos passaram a ser muito mais realistas, também é perceptivel mudanças na média. Considerando que temos mais de 19 mil registros, uma mudança na média passa a ser muito significativo.
# 
# Observação: Não foi aplicado IQR em 'lights' por uma baixa concentração de outliers, também ocorre que ao aplicar IQR em 'lights', todos os valores são zerados.

# In[87]:


dtProcessado_IQR.describe()


# ## 5.4 Feature Scaling

# ### 5.4.1 Aplicando Padronização

# Para os algoritmos que iremos utilizar como SVM, XGBoost e Regressão Logística Multilinear a padronização se mostra mais relevante. Como nossas variaveis 

# In[88]:


# Padronização dos dados
scaler = StandardScaler()
processado_IQR_padronizado = dtProcessado_IQR.copy()
processado_IQR_padronizado[quantitativas.drop('Appliances')] = scaler.fit_transform(                                                                    dtProcessado_IQR[quantitativas.drop('Appliances')])


# In[89]:


'''
# Padronização dos dados
scaler = StandardScaler()
processado_IQR_padronizado = dtProcessado_IQR.copy()
processado_IQR_padronizado[quantitativas] = scaler.fit_transform(dtProcessado_IQR[quantitativas])
'''


# Após realizar a padronização dos dados, iremos revisitar algumas metricas como skewness, kurtose e boxplot stats.

# In[90]:


dtProcessado_IQR_padronizado = pd.DataFrame(processado_IQR_padronizado.copy(), columns = dtProcessado_IQR.columns)


# In[91]:


dtProcessado_IQR_padronizado.head()


# ### 5.4.2 Analisando Dados Pós Padronização

# Verificando novamente o skewness, tivemos um aumento consideravel na simetria dos dados, conseguimos reduzir o nosso Skewness total pela metade, o que deve levar a melhores resultados para os algoritmos. Iremos realizar a analise de suas vantagens posteriormente na aplicação dos algoritmos.

# In[92]:


print(dtProcessado_IQR_padronizado.skew()[quantitativas],      '\nSoma:', sum(abs(dtProcessado_IQR_padronizado[quantitativas].skew())))


# Verificando novamente a Kurtosis possuimos uma perspectiva muito melhor, conseguimos ajustar as respectivas kurtosis para proximo de 3, trazendo uma distribuição normal Gaussiana, isso se da pela padronização dos dados. A soma ideal da Kurtosis para as nossas 27 variaveis seria 0, chegamos em um valor bem proximo.

# In[93]:


print(dtProcessado_IQR_padronizado[quantitativas].kurtosis(),      '\nSoma:', sum(abs(dtProcessado_IQR_padronizado[quantitativas].kurtosis())))


# Percebemos uma melhora significativa no histograma abaixo das variaveis, com exceção de lights que manteve um skewness alto.

# In[94]:


hist_individual(dtProcessado_IQR_padronizado, quantitativas[0:9])


# In[95]:


hist_individual(dtProcessado_IQR_padronizado, quantitativas[9:18])


# In[96]:


hist_individual(dtProcessado_IQR_padronizado, quantitativas[18:27])


# Já em relação aos outliers, com a aplicação de IR e correçõs nas escalas dos dados conseguimos uma redução perceptivel.
# 
# Observação: Não foi aplicado correção de outliers por IQR na variavel 'lights'.

# In[97]:


boxplot_individuais(dtProcessado_IQR_padronizado, quantitativas[0:9])


# In[98]:


boxplot_individuais(dtProcessado_IQR_padronizado, quantitativas[9:18])


# In[99]:


boxplot_individuais(dtProcessado_IQR_padronizado, quantitativas[18:27])


# ## 5.5 Incremento nas Features

# Aqui iremos acrescentar mais uma variavel no nosso dataset que irá merecer uma analise na etapa de Feature Selection. Iremos acrescentar uma Feature do tipo booleana para os feriados no de coleta dos dados.

# In[100]:


feriados = []

# Criando lista com todos feriados do ano em que o dataset foi gerado
for data in Belgium(years = [2016]).items():
    feriados.append(data)


# In[101]:


# Converter para dataframe e renomear colunas
dtferiados = pd.DataFrame(feriados)
dtferiados.columns = ['data', 'feriado']


# In[102]:


dtferiados.head()


# In[103]:


# Criar uma copia do dataset original para recuperar a coluna 'date', desconsiderando horario
dtTemp = dtFull.copy()
dtTemp['date'] = pd.to_datetime(dtTemp['date'], format='%Y-%m-%d %H:%M:%S').dt.date


# In[104]:


def isHoliday(row):
    
    # Verifica se a data da linha atual esta no dataframe de feriados
    holiday = dtferiados.apply(lambda x: 1 if (row['date'] == x['data']) else 0, axis = 1)
    
    holiday = sum(holiday)
    
    if holiday > 0:
        holiday = 1
    else:
        holiday = 0
    
    return holiday


# In[105]:


# Preenche a coluna feriados do dataframe temporario
dtTemp['Holiday'] = dtTemp.apply(isHoliday, axis = 1)


# In[106]:


# Copia a coluna de feriados do dataframe temporario para o novo
dtProcessado_incremento = dtProcessado_IQR_padronizado.copy()
dtProcessado_incremento['Holiday'] = dtTemp['Holiday'].copy().values


# Como verificado abaixo criamos uma variavel boolean para os dias que forem feriado, onde pode ocorrer um aumento do consumo de energia. 

# In[107]:


dtProcessado_incremento.head()


# Por ultimo iremos remover a variavel 'lights' por não fazer sentido estar no modelo, visto que a mesma apresenta o consumo de Wh das fontes luz da residencia, assim nos indicando um pouco do consumo de energia.

# In[108]:


dtFinal = dtProcessado_incremento.drop('lights', axis = 1)


# # 6. Feature Selecting

# Após uma densa etapa de analise exploratoria e pre-processamento iremos iniciar a etapa de seleção de variaveis, onde iremos ter que trabalhar densamente para eliminar multicolinearidade escolher variaveis que trazem valor para o nosso problema.
# 
# Sobre a regressão Lasso e Ridge, iremos utilizar a Lasso com uma das alternativas para medir a importancia das variaveis. Já a ressão Ridge, iremos utilizar durante a modelagem preditiva para tentar aumentar a importancia das variaveis corretas.

# In[109]:


dtFinal.columns


# ## 6.1 Select From Model - Random Forest

# Iremos utilizar o SelectModel para secionarmos as variaveis baseadas em sua importância, posteriormente iremos realizar o plot de importância por variavel.

# In[109]:


X_fs = dtFinal.drop(['Appliances'], axis = 1)
y_fs = dtFinal['Appliances'].values


# In[110]:


seleciona_fs = SelectFromModel(RandomForestRegressor())
seleciona_fs.fit(X_fs, y_fs)


# In[111]:


variaveis = X_fs.columns[seleciona_fs.get_support()]


# In[112]:


print(variaveis)


# ## 6.2 Random Forest - Feature Importance

# Agora iremos utilizar o Random Forest na sua forma pura, sem hiperparametros. Essa forma é um pouco perigosa pois pode gerar vies do modelo, por isso iremos testar posteriormente com um modelo diferente.

# In[113]:


modelo_fs_v1 = RandomForestRegressor()
modelo_fs_v1.fit(X_fs, y_fs)


# In[114]:


index_ordenado_fs_v1 = modelo_fs_v1.feature_importances_.argsort()


# Analisando, possuimos a variavel 'NSM' com a maior importancia muito a frente, seguido por 'Hour' e 'Lights'. O SelectModel analisou que as melhores variaveis seriam as: 'lights', 'T3', 'RH_3', 'T8', 'Press_mm_hg', 'NSM' e 'Hour'.
# 
# Dessa forma escolhendo as 7 variaveis com maior importancia.

# In[115]:


plt.barh(dtFinal.drop(['Appliances'], axis = 1).columns[index_ordenado_fs_v1],         modelo_fs_v1.feature_importances_[index_ordenado_fs_v1])


# ## 6.3 Regressão LASSO

# Iremos utilizar a Regressão LASSO para minimizar variaveis, assim podemos diminuir a nossa dimensionalidade e multicolinearidade, de forma que o modelo se torne mais generalizado.

# In[116]:


# Função para calcular o RMSE
def rmse_cv(modelo, x, y):
    rmse = np.sqrt(-cross_val_score(modelo, 
                                    x, 
                                    y, 
                                    scoring = "neg_mean_squared_error", 
                                    cv = 5))
    return(rmse)


# In[117]:


# Criando modelo LASSO, com lista de alphas e executanndo em CV
modelo_fs_v2 = LassoCV(alphas = [10, 1, 0.1, 0.01, 0.001])
modelo_fs_v2.fit(X_fs, y_fs)


# In[118]:


# Calculando RMSE de todos os CV
rmse = rmse_cv(modelo_fs_v2, X_fs, y_fs)


# In[119]:


# Print valor medio, maximo, minimo
print(rmse.mean(), max(rmse), min(rmse))


# In[120]:


# Coeficientes LASSO
coef = pd.Series(modelo_fs_v2.coef_, index = X_fs.columns)


# In[121]:


coef.sort_values().tail(15)


# In[122]:


# Plotando importancia das variaveis
imp_coef_fs = pd.concat([coef.sort_values().head(15), coef.sort_values().tail(15)])
matplotlib.rcParams['figure.figsize'] = (8.0, 10.0)
imp_coef_fs.plot(kind = "barh")
plt.title("Coeficientes Modelo LASSO")


# ## 6.4 Recursive Feature Elimination (RFE) - Linear SVR

# Como quarto metodo, iremos utilizar RFE, onde em geral apresenta bons resultados para combater multicolinearidade que é o nosso principal problema nesse dataset. Porém, o seu tempo de execução pode ser muito grande.

# In[123]:


# Criando modelo de SVM para regressão
modelo_v4 = LinearSVR(max_iter = 3000)
rfe = RFE(modelo_v4, n_features_to_select = 8)


# In[124]:


# Treinando RFE
rfe.fit(X_fs, y_fs)


# In[125]:


print('Features Selecionadas: %s' % rfe.support_)
print("Feature Ranking: %s" % rfe.ranking_)


# In[126]:


variaveis_v4 = [X_fs.columns[i] for i, col in enumerate(rfe.support_) if col == True]


# In[127]:


print(variaveis_v4)


# In[128]:


X_fs[variaveis_v4].head()


# ## 6.5 Analisando Seleção

# In[129]:


def avalia_modelo(modelo, x, y):  
    preds = modelo.predict(x)
    
    erros = abs(preds - y)
    mape = 100 * np.mean(erros / y)
    r2 = 100*r2_score(y, preds)
    acuracia = 100 - mape
    mse = mean_squared_error(y, preds, squared = True)
    mae = mean_absolute_error(y, preds)
    rmse = mean_squared_error(y, preds, squared = False)
    
    print(modelo,'\n')
    print('R^2                 : {:0.2f}%' .format(r2))
    print('Acuracia            : {:0.2f}%'.format(acuracia))
    print('MAE                 : {:0.2f}'.format(mae))
    print('MSE                 : {:0.2f}'.format(mse))
    print('RMSE                : {:0.2f}\n'.format(rmse))


# ### 6.5.1 Random Forest

# In[130]:


# Selecionando variaveis do RandomForestRegressor
X_sel_fs_v1 = X_fs[variaveis]


# In[131]:


x_train, x_test, y_train, y_test = train_test_split(X_fs, y_fs, test_size = .3, random_state = seed_)


# Primeiramente iremos avaliar o modelo com todas as variaveis utilizadas durante a sua construção.

# In[132]:


# Criando o modelo com todas variaveis
modelo_sel_fs_v1 = RandomForestRegressor()
modelo_sel_fs_v1.fit(x_train, y_train)


# In[133]:


avalia_modelo(modelo_sel_fs_v1, x_test, y_test)


# In[134]:


x_train, x_test, y_train, y_test = train_test_split(X_sel_fs_v1, y_fs, test_size = .3, random_state = seed_)


# In[135]:


# Criando o modelo com variaveis selecionodas pelo RandomForestRegressor
modelo_sel_fs_v2 = RandomForestRegressor()
modelo_sel_fs_v2.fit(x_train, y_train)


# Avaliando o modelo utilizando somente 6 colunas, mantivemos um R^2 de 70% com um aumento para 23 do RMSE. Apesar do modelo ser um pouco pior, aumentamos a nossa generalização em muito, visto que passamos de 31 variaveis para 6 variaveis.

# In[136]:


avalia_modelo(modelo_sel_fs_v2, x_test, y_test)


# In[137]:


i = 20
x_temp = x_test.iloc[i]
x_temp = pd.DataFrame(x_temp).T
y_temp = y_test[i]


# In[138]:


pred = modelo_sel_fs_v2.predict(x_temp)


# In[139]:


print('Previsto:', pred,'Real:', y_temp)


# ### 6.5.2 LASSO

# In[140]:


X_sel_fs_v2 = X_fs[['RH_1', 'T3', 'T6', 'T8', 'RH_3']]


# In[141]:


x_train, x_test, y_train, y_test = train_test_split(X_fs, y_fs, test_size = .3, random_state = seed_)


# Primeiramente iremos avaliar o modelo com todas as variaveis utilizadas durante a sua construção.

# In[142]:


# Criando modelo LASSO, com todas variaveis
modelo_sel_fs_v3 = LassoCV(alphas = [10, 1, 0.1, 0.01, 0.001])
modelo_sel_fs_v3.fit(x_train, y_train)


# In[143]:


avalia_modelo(modelo_sel_fs_v3, x_test, y_test)


# In[144]:


x_train, x_test, y_train, y_test = train_test_split(X_sel_fs_v2, y_fs, test_size = .3, random_state = seed_)


# In[145]:


# Criando modelo LASSO, com variaveis selecionadas
modelo_sel_fs_v4 = LassoCV(alphas = [1, 0.1, 0.001, 0.0005])
modelo_sel_fs_v4.fit(x_train, y_train)


# Analisando o modelo é perceptivel que ele não conseguiu representar os dados da forma adequada, mantendo um R^2 abaixo de 50%, com acuracia pouco acima de 50%.

# In[146]:


avalia_modelo(modelo_sel_fs_v4, x_test, y_test)


# ### 6.5.3 RFE - Linear SVR

# In[147]:


# Selecionando variaveis do RandomForestRegressor
X_sel_fs_v3 = X_fs[variaveis_v4]


# In[148]:


x_train, x_test, y_train, y_test = train_test_split(X_fs, y_fs, test_size = .3, random_state = seed_)


# In[149]:


# Criando o modelo com todas variaveis
modelo_sel_fs_v3 = LinearSVR(max_iter = 3000)
modelo_sel_fs_v3.fit(x_train, y_train)


# Analisando o modelo com todas variaveis, o deu desempenho não aparenta ser bom visto que manteve um R^2 abaixo de 50% e alto RMSE, apesar disso apresentou uma acuracia superior ao modelo de regressão LASSO.

# In[150]:


avalia_modelo(modelo_sel_fs_v3, x_test, y_test)


# In[151]:


x_train, x_test, y_train, y_test = train_test_split(X_sel_fs_v3, y_fs, test_size = .3, random_state = seed_)


# In[152]:


# Criando o modelo com todas variaveis
modelo_sel_fs_v3 = LinearSVR(max_iter = 3000)
modelo_sel_fs_v3.fit(x_train, y_train)


# In[153]:


avalia_modelo(modelo_sel_fs_v3, x_test, y_test)


# Realizando a analise acima é perceptivel que as variaveis que aparentam trazer mais representatividade para o nosso modelo são as do modelo de Random Forest, esse que sugeriu utilizar as seguintes variaveis:
# 
# 'T3', 'RH_3', 'T8', 'Press_mm_hg', 'NSM' e 'Hour'
# 
# Analisando as variaveis acima:
# 'T3' -> Mede a temperatura em graus celsius na lavanderia, a lavanderia constuma possuir equipamentos que consomem um nivel de energia significativamente maior do que outros eletrodomesticos, assim também aumenta o nivel de calor no comodo.
# 
# 'RH_3' -> Umidade relativa na lavanderia, indicando aumento da umidade no ambiente, também por conta dos eletrodomesticos utilizados no ambiente.
# 
# 'T8' -> Temperatura no quarto do adolescente.
# 
# 'Press_mm_hg' -> Pressão.
# 
# 'NSM' -> Quantos segundos faltam para a meia noite, visto que quando mais proximo da meia noite menor o consumo de energia.
# 
# 'Hour' -> Semelhante a 'NSM' porém indicando a forma do dia de forma mais especifica, visto que a hora influencia diretamente no consumo de energia.

# # 7. Modelagem Preditiva

# ## 7.1 Definindo Ambiente

# In[110]:


# Separando em variaveis preditivas e target 
#X = dtFinal[variaveis]
X = dtFinal[['T3', 'RH_3', 'T8', 'Press_mm_hg', 'NSM', 'Hour']]
y = dtFinal['Appliances'].values


# In[111]:


X.head()


# In[112]:


y


# In[113]:


# Separando em treino e teste
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size = 0.3, random_state = seed_)


# In[114]:


def reportModeloRegressao(modelo, x_teste, y_teste, x_treino = [], y_treino = [], report_treino = False):  
    y_pred = modelo.predict(x_teste)
    
    erros = abs(y_pred - y_teste)
    mape = 100 * np.mean(erros / y_teste)
    r2 = 100*r2_score(y_teste, y_pred)
    r2_ajustado = 1 - (1 - r2) * (len(y_teste) - 1) / (len(y_teste) - x_teste.shape[1] -1)
    acuracia = 100 - mape
    mse = mean_squared_error(y_teste, y_pred, squared = True)
    mae = mean_absolute_error(y_teste, y_pred)
    rmse = mean_squared_error(y_teste, y_pred, squared = False)
    
    print(modelo,'\n')
    print('Dados de teste')
    print('R^2                 : {:0.2f}%' .format(r2))
    print('R^2 Ajustado        : {:0.2f}%' .format(r2_ajustado))
    print('Acuracia            : {:0.2f}%'.format(acuracia))
    print('MAE                 : {:0.2f}'.format(mae))
    print('MSE                 : {:0.2f}'.format(mse))
    print('RMSE                : {:0.2f}\n'.format(rmse))
    
    residuo = abs(y_teste - y_pred)
    plt.scatter(residuo, y_pred)
    plt.xlabel('Residuos')
    plt.ylabel('Previsto')
    plt.show()
    
    if report_treino:
        print('Dados de treino')
        if x_treino.shape[1] > 0 and len(y_treino) > 0: 
            reportModeloRegressao(modelo, x_treino, y_treino)
        else:
            print('X_treino e/ou y_treino possuem tamanho 0.')


# In[115]:


def treinaRegressao_GridSearchCV(modelo, params_, x_treino, y_treino, x_teste, y_teste,                        n_jobs = -1, cv = 5, refit = True, scoring = None, salvar_resultados = False,                       report_treino = False):
    grid = GridSearchCV(modelo, params_, n_jobs = n_jobs, cv = cv, refit = refit, scoring = scoring)
    
    grid.fit(x_treino, y_treino)
    pred = grid.predict(x_teste)
    modelo_ = grid.best_estimator_

    print(grid.best_params_)
    
    reportModeloRegressao(modelo_, x_teste, y_teste, x_treino, y_treino, report_treino) 
    
    if salvar_resultados:
        resultados_df = pd.DataFrame(grid.cv_results_)
        
        return resultados_df 


# ## 7.2 SVR

# Primeiramente iremos criar um modelo base utilizando o algoritmo SVM para regressão, conhecido como SVR. Assim, iremos poder ter uma metrica minima para comparar os nossos modelos, posteriormente iremos passar por uma fase de tuning dos hiperparametros, utilizaando GridSearchCV e depois um tuning manual.

# In[115]:


# Modelo base do algoritmo SVM para regressão
modelo_svr = SVR(max_iter = -1)
modelo_svr.fit(x_train, y_train)


# Apesar da nossa acuracia base ser 67%, estamos com um R^2 muito baixo de apenas 20.75%. Iremos tentar diminuor o nosso RMSE na medida que aumentamos o R^2.

# In[116]:


reportModeloRegressao(modelo_svr, x_test, y_test, x_train, y_train, True)


# In[162]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'kernel': ['linear', 'poly', 'rbf', 'sigmoid'],\n    'C': [0.9, 1.0, 1.1],\n    'gamma': ['scale', 'auto']\n}\n\n# Criação de modelo intenso 01\nmodelo = SVR(max_iter = -1, cache_size = 1000)\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[163]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'kernel': ['rbf'],\n    'C': [0.001, 0.1, 1.0, 10, 100],\n    'gamma': ['auto']\n}\n\n# Criação de modelo intenso 02\nmodelo = SVR(max_iter = -1, cache_size = 1000)\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[164]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'kernel': ['rbf'],\n    'C': [0.1, 1.0, 10, 100, 1000, 10000],\n    'gamma': ['auto']\n}\n\n# Criação de modelo intenso 03\nmodelo = SVR(max_iter = -1, cache_size = 1000)\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[165]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'kernel': ['rbf'],\n    'C': [500, 1000, 2000],\n    'gamma': ['auto']\n}\n\n# Criação de modelo intenso 04\nmodelo = SVR(max_iter = -1, cache_size = 1000)\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[117]:


get_ipython().run_cell_magic('time', '', "# Modelo 05\nmodelo_svr_v5 = SVR(max_iter = -1, cache_size = 1000, kernel = 'rbf', C = 10000, gamma = 'auto')\nmodelo_svr_v5.fit(x_train, y_train)\n\nreportModeloRegressao(modelo_svr_v5, x_test, y_test, x_train, y_train, True)")


# In[124]:


get_ipython().run_cell_magic('time', '', "# Modelo 06\nmodelo_svr_v6 = SVR(max_iter = -1, cache_size = 1000, kernel = 'rbf', C = 10000, gamma = 1) # gamma = 'auto' = 0.166\nmodelo_svr_v6.fit(x_train, y_train)\n\nreportModeloRegressao(modelo_svr_v6, x_test, y_test, x_train, y_train, True)")


# In[126]:


get_ipython().run_cell_magic('time', '', "# Modelo 07\nmodelo_svr_v7 = SVR(max_iter = -1, cache_size = 1000, kernel = 'rbf', C = 10000, gamma = 3) # gamma = 'auto' = 0.166\nmodelo_svr_v7.fit(x_train, y_train)\n\nreportModeloRegressao(modelo_svr_v7, x_test, y_test, x_train, y_train, True)")


# In[127]:


get_ipython().run_cell_magic('time', '', "# Modelo 08\nmodelo_svr_v8 = SVR(max_iter = -1, cache_size = 1000, kernel = 'rbf', C = 10000, gamma = 0.5) # gamma = 'auto' = 0.166\nmodelo_svr_v8.fit(x_train, y_train)\n\nreportModeloRegressao(modelo_svr_v8, x_test, y_test, x_train, y_train, True)")


# ### 7.2.1 Conclusão SVR

# Executando o algoritmo SVR, conseguimos atingir as seguintes metricas sem evitar overfitting:
# 
# - R^2                 : 56.06%
# - R^2 Ajustado        : 56.12%
# - Acuracia            : 76.01%
# - MAE                 : 17.26
# - MSE                 : 797.83
# - RMSE                : 28.25
# 
# Apesar de atingirmos um RMSE relativamente baixo de 28 unidades, não possuimos uma boa acuracia, estando apenas em 75%. Ainda possuimos um R^2 baixo, de apenas 56%.
# 
# O algoritmo SVR necessita de uma alta carga de processamento, chegando a possuir testes em que os resultados demoravam mais de 1 hora para serem gerados. Para melhor compreensão foram exibidos nesse documento somente os algoritmos de maior influência.
# 
# O algoritmo SVR, não apresentou bom desempenho, devido a alta variabilidade nos dados, que não conseguiram ser identificados da forma ideal. Assim, iremos adotar a eestratégia de utilizar algoritmos ensemble, como XGBoost e CatBoost da categoria boosting.

# ### 7.2.2 Executando Melhor Modelo

# In[129]:


get_ipython().run_cell_magic('time', '', "# Modelo Final\nmodelo_svr_final = SVR(max_iter = -1, cache_size = 1000, kernel = 'rbf', C = 10000, gamma = 0.5) # gamma = 'auto' = 0.166\nmodelo_svr_final.fit(x_train, y_train)\n\nreportModeloRegressao(modelo_svr_final, x_test, y_test, x_train, y_train, True)")


# ### 7.2.3 Avaliando SVR

# In[115]:


shap.initjs()


# In[135]:


# Construindo shap
amostras = 20
explainer = shap.Explainer(modelo_svr_final.predict, x_train)
shap_values = explainer(x_test[:amostras])


# In[149]:


# Waterfall Predição 0
shap.plots.waterfall(shap_values[0])


# In[152]:


# Waterfall Predição 10
shap.plots.waterfall(shap_values[10])


# In[155]:


# Force Predição 0
shap.plots.force(shap_values[0])


# In[156]:


# Force Predição 10
shap.plots.force(shap_values[10])


# In[188]:


# Summary Plot
shap.summary_plot(shap_values, x_test[:amostras])


# ## 7.3 CatBoost Regressor

# ### 7.3.1 Definindo Ambiente

# In[118]:


# Separando o conjunto de treino em treino e validação
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, train_size = 0.8, random_state = seed_)


# In[119]:


# Definindo variaveis categoricas
categorical_features_index = np.where(x_train.dtypes != np.float)[0]


# ### 7.3.2 Iniciando Modelagem

# In[128]:


get_ipython().run_cell_magic('time', '', "# Modelo Base CatBoost Regressor\nmodelo_cat = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_)\n\nmodelo_cat.fit(x_train, y_train,\n               cat_features = categorical_features_index,\n               eval_set = (x_val, y_val),\n               plot = True, verbose = False);")


# Comparando com o melhor modelo gerado no tuning do algoritmo SVR, o modelo base do Catboost já possui um desempenho superior com maior R^2 Ajustado e menor RMSE e MSE.

# In[130]:


reportModeloRegressao(modelo_cat, x_test, y_test, x_train, y_train, True)


# In[120]:


get_ipython().run_cell_magic('time', '', "# Modelo 01 CatBoost Regressor\nmodelo_cat_v1 = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                                 iterations = 5000, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\nmodelo_cat_v1.fit(x_train, y_train,\n               cat_features = categorical_features_index,\n               eval_set = (x_val, y_val),\n               plot = True, verbose = True);")


# In[121]:


reportModeloRegressao(modelo_cat_v1, x_test, y_test, x_train, y_train, True)


# In[122]:


get_ipython().run_cell_magic('time', '', "# Modelo 03 CatBoost Regressor\nmodelo_cat_v3 = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                                 iterations = 5000, metric_period = 50, od_type = 'Iter', od_wait = 20,\\\n                                 learning_rate = 0.01)\n\nmodelo_cat_v3.fit(x_train, y_train,\n               cat_features = categorical_features_index,\n               eval_set = (x_val, y_val),\n               plot = True, verbose = False);")


# In[123]:


reportModeloRegressao(modelo_cat_v3, x_test, y_test, x_train, y_train, True)


# In[125]:


get_ipython().run_cell_magic('time', '', "# Modelo 04 CatBoost Regressor\nmodelo_cat_v4 = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                                 iterations = 5000, metric_period = 50, od_type = 'Iter', od_wait = 20,\\\n                                 learning_rate = 0.1)\n\nmodelo_cat_v4.fit(x_train, y_train,\n               cat_features = categorical_features_index,\n               eval_set = (x_val, y_val),\n               plot = True, verbose = False);")


# In[126]:


reportModeloRegressao(modelo_cat_v4, x_test, y_test, x_train, y_train, True)


# In[131]:


get_ipython().run_cell_magic('time', '', "# Modelo 05 CatBoost Regressor\nmodelo_cat_v5 = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                                 iterations = 20000, metric_period = 50, od_type = 'Iter', od_wait = 20,\\\n                                 learning_rate = 0.01)\n\nmodelo_cat_v5.fit(x_train, y_train,\n               cat_features = categorical_features_index,\n               eval_set = (x_val, y_val),\n               plot = True, verbose = False);\n\nreportModeloRegressao(modelo_cat_v5, x_test, y_test, x_train, y_train, True)")


# In[138]:


# Separando em variaveis preditivas e target 
#X = dtFinal[variaveis]
X = dtFinal[['T3', 'RH_3', 'T8', 'Press_mm_hg', 'NSM', 'Hour']]
y = dtFinal['Appliances'].values

# Separando em treino e teste
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size = 0.3, random_state = seed_)


# In[141]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [5, 6, 7, 8, 9],\n    'learning_rate': [0.01, 0.05, 0.1, 0.2],\n    'iterations' : [5000]\n}\n\n# Criação de modelo intenso 06\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[142]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [7, 8, 9, 10],\n    'learning_rate': [0.04, 0.05, 0.06, 0.07],\n    'iterations' : [5000]\n}\n\n# Criação de modelo intenso 07\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[143]:


# Separando em variaveis preditivas e target 
#X = dtFinal[variaveis]
X = dtFinal[['T3', 'RH_3', 'T8', 'Press_mm_hg', 'NSM', 'Hour']]
y = dtFinal['Appliances'].values

# Separando em treino e teste
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size = 0.3, random_state = seed_)

# Separando o conjunto de treino em treino e validação
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, train_size = 0.8, random_state = seed_)


# In[144]:


get_ipython().run_cell_magic('time', '', "# Modelo 08 CatBoost Regressor\nmodelo_cat_v8 = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                                 iterations = 5000, metric_period = 50, od_type = 'Iter', od_wait = 20,\\\n                                 learning_rate = 0.05, depth = 10)\n\nmodelo_cat_v8.fit(x_train, y_train,\n               cat_features = categorical_features_index,\n               eval_set = (x_val, y_val),\n               plot = True, verbose = False);\n\nreportModeloRegressao(modelo_cat_v8, x_test, y_test, x_train, y_train, True)")


# In[145]:


# Separando em variaveis preditivas e target 
#X = dtFinal[variaveis]
X = dtFinal[['T3', 'RH_3', 'T8', 'Press_mm_hg', 'NSM', 'Hour']]
y = dtFinal['Appliances'].values

# Separando em treino e teste
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size = 0.3, random_state = seed_)


# In[147]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [8, 9, 10],\n    'learning_rate': [0.04, 0.05, 0.06],\n    'grow_policy': ['Depthwise', 'Lossguide'],\n    'iterations' : [5000]\n}\n\n# Criação de modelo intenso 09\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[148]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [9, 10],\n    'learning_rate': [0.02, 0.03, 0.04],\n    'grow_policy': ['Depthwise'],\n    'iterations' : [5000]\n}\n\n# Criação de modelo intenso 10\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[149]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [10, 11],\n    'learning_rate': [0.025, 0.03, 0.035],\n    'grow_policy': ['Depthwise'],\n    'iterations' : [5000]\n}\n\n# Criação de modelo intenso 11\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[151]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [11],\n    'learning_rate': [0.024, 0.025, 0.026],\n    'grow_policy': ['Depthwise'],\n    'iterations' : [5000]\n}\n\n# Criação de modelo intenso 12\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[153]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [11],\n    'langevin': [True],\n    'diffusion_temperature': [9000, 10000, 11000],\n    'learning_rate': [0.025],\n    'grow_policy': ['Depthwise'],\n    'iterations' : [5000]\n}\n\n# Criação de modelo intenso 13\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[154]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [11],\n    'langevin': [True],\n    'diffusion_temperature': [10000],\n    'learning_rate': [0.2, 0.22, 0.025, 0.27],\n    'grow_policy': ['Depthwise'],\n    'iterations' : [5000]\n}\n\n# Criação de modelo intenso 14\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[155]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [11],\n    'langevin': [True],\n    'diffusion_temperature': [10000],\n    'learning_rate': [0.025],\n    'grow_policy': ['Depthwise'],\n    'iterations' : [5000],\n    # Não foi adicionado a score function 'Cosine', pois essa é a default utilizada no modelo 14\n    'score_function': ['L2', 'NewtonCosine', 'NewtonL2']\n}\n\n# Criação de modelo intenso 15\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# # TO DO
# - Tuning: feature_weights

# In[118]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [11],\n    'langevin': [True],\n    'diffusion_temperature': [10000],\n    'learning_rate': [0.025],\n    'grow_policy': ['Depthwise'],\n    'iterations' : [5000],\n    'score_function': ['Cosine'],\n    'l2_leaf_reg': [2.5]\n}\n\n# Criação de modelo intenso 16\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[117]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [11],\n    'langevin': [True],\n    'diffusion_temperature': [10000],\n    'learning_rate': [0.025],\n    'grow_policy': ['Depthwise'],\n    'iterations' : [5000],\n    'score_function': ['Cosine'],\n    'l2_leaf_reg': [2.4, 2.6, 2.8]\n}\n\n# Criação de modelo intenso 17\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[119]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [11],\n    'langevin': [True],\n    'diffusion_temperature': [10000],\n    'learning_rate': [0.025],\n    'grow_policy': ['Depthwise'],\n    'iterations' : [5000],\n    'score_function': ['Cosine'],\n    'l2_leaf_reg': [2.5],\n    'subsample': [0.7, 0.9, 1.0] # Default subsample = 0.8\n}\n\n# Criação de modelo intenso 18\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[116]:


get_ipython().run_cell_magic('time', '', "\nparams = {\n    'depth': [11],\n    'langevin': [True],\n    'diffusion_temperature': [10000],\n    'learning_rate': [0.025],\n    'grow_policy': ['Depthwise'],\n    'iterations' : [5000],\n    'score_function': ['Cosine'],\n    'l2_leaf_reg': [2.5],\n    'subsample': [0.8],\n    'bootstrap_type': ['Bayesian', 'Bernoulli', 'No'] # Default para CPU = MVS\n}\n\n# Criação de modelo intenso 19\nmodelo = CatBoostRegressor(loss_function = 'RMSE', eval_metric = 'RMSE', random_seed = seed_,\\\n                           verbose = False, metric_period = 50, od_type = 'Iter', od_wait = 20)\n\ntreinaRegressao_GridSearchCV(modelo, params, x_train, y_train, x_test, y_test, scoring = 'neg_root_mean_squared_error',\\\n                            report_treino = True)")


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:



