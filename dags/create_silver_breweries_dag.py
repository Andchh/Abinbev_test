from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, trim, regexp_replace, current_timestamp
import os
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_silver_transformation():

    # Configuração do Spark em modo local forçado para evitar problemas de cluster
    spark = (SparkSession.builder
             .appName("create_silver_breweries")
             .master("local[*]")  
             .config("spark.driver.memory", "1g")  
             .config("spark.executor.memory", "1g")
             .config("spark.sql.files.ignoreCorruptFiles", "true")
             .config("spark.driver.maxResultSize", "500m") 
             .config("spark.rpc.message.maxSize", "128")  
             .getOrCreate())

    bronze_path = "/opt/airflow/datalake/bronze"
    silver_path = "/opt/airflow/datalake/silver"

    try:
        # Verificar se o diretório bronze existe
        if not os.path.exists(bronze_path):
            raise FileNotFoundError(f"O diretório bronze não existe: {bronze_path}")
        
        # Criar diretório silver se não existir
        os.makedirs(silver_path, exist_ok=True)
        
        # Leitura dos dados da camada bronze
        logger.info(f"Lendo dados da camada bronze: {bronze_path}")
        df = (spark.read
              .option("multiline", "true")
              .option("mode", "PERMISSIVE") 
              .option("columnNameOfCorruptRecord", "_corrupt_record")
              .json(bronze_path))
        
        # Verificar se temos dados
        count = df.count()
        if count == 0:
            raise ValueError("Nenhum dado foi carregado do diretório bronze")
        
        # Aplicar normalizações
        logger.info("Aplicando normalizações aos dados")
        
        # Normalização de colunas de localização
        for column in ["country", "state", "city"]:
            logger.info(f"Normalizando coluna: {column}")
            df = df.withColumn(column, 
                             regexp_replace(lower(trim(col(column))), r"[^a-z0-9]+", "_"))
        
        # Adicionar timestamp de processamento
        df = df.withColumn("processed_at", current_timestamp())
        
        # Escrita particionada por pais, estado e cidade (localização)
        logger.info(f"Salvando dados normalizados na camada silver: {silver_path}")
        df.write.mode("overwrite").partitionBy("country", "state", "city").parquet(silver_path)
        
        logger.info("Escrita concluida.")
        
    except FileNotFoundError as e:
        logger.error(f"Erro de arquivo não encontrado: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Erro de valor: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Erro não esperado durante o processamento: {str(e)}")
        raise
    finally:
        logger.info("Encerrando sessão Spark")
        spark.stop()

if __name__ == "__main__":
    try:
        run_silver_transformation()
    except Exception as e:
        logger.error(f"Falha na execução: {str(e)}")
        # Retorna código de erro para o Airflow saber que falhou
        exit(1)