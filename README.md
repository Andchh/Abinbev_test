# 🚀 Projeto Airflow com Docker

Este projeto utiliza o Apache Airflow em um ambiente Dockerizado para orquestração de pipelines de dados. É ideal para desenvolvimento local, testes e aprendizado.
Este projeto utiliza Apache Airflow  e Spark em um ambiente Docker para orquestração de pipeline de dados.
Ele foi criado para o desafio técnico para a empresa AbInbev.

O airflow foi escolhido por ser uma ferramenta conhecida tanto na área de individual como em grandes empresas, facilitando uma simulação para um mundo corporativo.
O docker permite que o projeto que foi criado e configurado de um jeito específico possa rodar em qualquer máquina com o suporte para o mesmo, facilitando o compartilhamento de código. Também é preciso considerar que sua rede interna pode ser configurada para simular a comunicação entre componentes geralmente usados para soluções de dados. Nesse projeto, por exemplo, o airflow poderia mandar o comando para o spark via rede local docker.
Python e Spark foram escolhidos como linguagens dessa solução por serem mais utilizadas no ramo de engenharia de dados. O python é usado para comunicação com a API, para mostrar sua eficiência como linguagem de script e o Spark é usado para tratamento de dados. No docker compose desse projeto também é possível criar diferentes workers para o spark, simulando uma rede com vários computadores trabalhando em paralelo para computar a solução. 

## 📁 Estrutura do Projeto

```
.
├── airflow/              # Configurações e arquivos internos do Airflow
├── config/               # Configurações gerais do projeto
├── dags/                 # DAGs do Airflow
├── logs/                 # Logs gerados pelo Airflow
├── notebooks/            # Notebooks Jupyter (opcional)
├── plugins/              # Plugins personalizados para o Airflow
├── spark/                # Scripts ou configs relacionados ao Apache Spark
├── var/                  # Dados variáveis usados no projeto
├── .env                  # Variáveis de ambiente
├── docker-compose.yml    # Orquestração de containers
├── Dockerfile            # Construção da imagem customizada
├── requirements.txt      # Dependências adicionais do Python
└── .gitignore            # Arquivos e pastas ignoradas pelo Git
```

## ✅ Pré-requisitos

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## ⚙️ Configuração

### 1. Clone o repositório
Crie uma pasta chamada brewer, execute o terminal dentro dela e clone o repositório com: 
```bash
git clone https://github.com/Andchh/brewer.git
cd brewer
```
Isso é importante para fins de compatibilidade e vai evitar erros por nome de volume.


### 2. Crie o arquivo `.env`

Você pode copiar um modelo existente ou criar manualmente um arquivo de texto e nomeá-lo .env dentro da pasta brewer que você baixou. Exemplo:

```bash
AIRFLOW_UID=50000
```
Porém o projeto já terá um arquivo .env pré definido com esse valor, considerando uma máquina com sistema operacional do Windows.
> Obs: `AIRFLOW_UID` pode ser obtido com `id -u` no Linux/macOS, ou definido como `50000` no Windows.

### 3. Suba os containers

```bash
docker-compose up --build
```

A primeira vez pode demorar alguns minutos, pois as imagens serão construídas e dependências instaladas.

### 4. Acesse o Airflow

Após os containers estarem rodando, acesse:

```
http://localhost:8080
```

Login padrão:

- **Usuário:** `airflow`
- **Senha:** `airflow`

### 5. Instalando dependências adicionais (opcional)

Adicione as bibliotecas necessárias ao `requirements.txt`, e elas serão instaladas no container do Airflow.

---

## 🛠 Comandos úteis

| Comando                          | Descrição                          |
|----------------------------------|------------------------------------|
| `docker-compose up`              | Inicia os containers               |
| `docker-compose down`            | Para os containers                 |
| `docker-compose logs -f`         | Visualiza logs em tempo real       |
| `docker-compose exec airflow-apiserver bash` | Acessa o terminal do Airflow     |
---
Esses comando podem variar baseado no nome da sua pasta. O Airflow pode criar, por exemplo, o airflow-apiserver como seufolder_airflow-apiserver. O projeto foi criado pensado em não depender desses nomes, porém é interessante saber que pode dar esse problema.

## 🧼 Reset do ambiente (⚠️ apaga dados)

```bash
docker-compose down -v
```

---

## Sobre o projeto e como testar

O projeto cria 3 Dags: 
* create_bronze_breweries

	Essa dag vai ler os dados da API em formato Json e salvá-los na pasta: ./airflow/datalake/bronze. O docker está configurado para copiar os arquivos desta pasta para o volume interno "datalake-volume".
	
* create_silver_breweries

	Esta dag vai esperar o fim da dag create_bronze_breweries e executar uma limpeza nos dados. As informações de localização (país, estados e cidade) não vem padronizadas, contendo assim abreviações, acentos ou tamanhos diferentes. Esse primeiro passo normaliza tudo para depois escrever os dados no formato colunar .parquet e particionado por localização (país, estado e cidade) na pasta .airflow/datalake/silver, que também é copiada para o volume interno "datalake-volume".
	
* create_gold_breweries

	Esta dag vai executar um script pyspark para gerar dados provindos de agregações. 
	Primeiro haverá a agregação por localização onde mostrará o número de cervejarias por localização (país, estado e cidade).
	Logo após o script também faz uma agregação por tipo de cervejaria. 
	Em seguida o script faz uma agregação por tipo e localização de cervejaria. 
	Assim, ao final de tudo os dados são salvos em formato .parquet na pasta ./airflow/datalake/gold, que também é copiada para o volume interno "datalake-volume". 

---
## Como testar após os dados escritos?

Para testes de dados é possível executar o spark-master dentro do docker, seguindo:

Execute um terminal dentro da pasta do projeto.
Procure o nome do spark-master com:
```bash
docker ps
```
Provavelmente vai aparecer como seufolder_spark-master-1. Para fins desse exemplo vamos usar brewer-spark-master-1 como exemplo.
Em seguida acesse o container do master com:

```bash
docker exec -it brewer-spark-master-1 bash
```
Isso vai nos proporcionar executar comandos bash dentro do container. Agora vamos ativar o pyspark com o comando simples:
```bash
pyspark
```
Agora podemos ler o arquivo .parquet com:
```bash
df = spark.read.parquet("/opt/airflow/datalake/gold/breweries_by_location")
```
Ou
```bash
df = spark.read.parquet("/opt/airflow/datalake/gold/breweries_by_type")
```
Ou
```bash
df = spark.read.parquet("/opt/airflow/datalake/gold/breweries_by_type_location")
```
E exibir os dados com:

```bash
df.show()
```

Pronto. 
Caso queira testar os dados das outras camadas é só mudar o caminho do spark.read para /opt/airflow/datalake/silver ou /opt/airflow/datalake/bronze.
Lembrando que, como a camada bronze está totalmente em "crua" em formato .json, então temos que mudar a forma de leitura para:


```bash
df = spark.read.option("multiline", "true").option("mode", "PERMISSIVE").option("columnNameOfCorruptRecord", "_corrupt_record").json("/opt/airflow/datalake/bronze")
```
---
