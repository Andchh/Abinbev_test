from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, lit, current_timestamp
import os
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_gold_transformation():
    """
    Cria uma visão agregada na camada Gold com a quantidade de cervejarias por tipo e localização.
    Esta transformação lê dados da camada Silver e produz tabelas agregadas para análise.
    """
    logger.info("Iniciando transformação silver -> gold")
    
    # Configuração do Spark em modo local forçado para evitar problemas de cluster
    spark = (SparkSession.builder
             .appName("create_gold_breweries_aggregated")
             .master("local[*]")  # Força modo local usando todos os cores disponíveis
             .config("spark.driver.memory", "1g")
             .config("spark.executor.memory", "1g")
             .config("spark.sql.session.timeZone", "UTC")
             .config("spark.sql.files.ignoreCorruptFiles", "true")
             .getOrCreate())
    

    silver_path = "/opt/airflow/datalake/silver"
    gold_path = "/opt/airflow/datalake/gold"
    
    try:
        # Verificar se o diretório silver existe
        if not os.path.exists(silver_path):
            raise FileNotFoundError(f"O diretório silver não existe: {silver_path}")
        
        # Criar diretório gold se não existir
        os.makedirs(gold_path, exist_ok=True)
        
        # Leitura dos dados da camada silver
        logger.info(f"Lendo dados da camada silver: {silver_path}")
        df = spark.read.parquet(silver_path)
        
        # Verificar se temos dados
        count = df.count()
        if count == 0:
            raise ValueError("Nenhum dado foi carregado do diretório silver")


        # 1. Agregação por país, estado e cidade
        logger.info("Criando agregação por localização (país, estado, cidade)")
        location_agg = (df
                        .groupBy("country", "state", "city")
                        .agg(count("*").alias("brewery_count"))
                        .withColumn("created_at", current_timestamp()))
        
        # Mostrar resultado da agregação por localização
        logger.info("Resultado da agregação por localização:")
        location_agg.show(10, truncate=False)
        
        # 2. Agregação por tipo de cervejaria
        logger.info("Criando agregação por tipo de cervejaria")
        type_agg = (df
                   .groupBy("brewery_type")
                   .agg(count("*").alias("brewery_count"))
                   .withColumn("created_at", current_timestamp()))
        
        # Mostrar resultado da agregação por tipo
        logger.info("Resultado da agregação por tipo:")
        type_agg.show(10, truncate=False)
        
        # 3. Agregação por tipo e localização combinados
        logger.info("Criando agregação por tipo e localização combinados")
        combined_agg = (df
                       .groupBy("brewery_type", "country", "state", "city")
                       .agg(count("*").alias("brewery_count"))
                       .withColumn("created_at", current_timestamp()))
        
        # Mostrar resultado da agregação combinada
        logger.info("Resultado da agregação combinada:")
        combined_agg.show(10, truncate=False)
        
        # Salvar agregações na camada gold
        logger.info("Salvando agregações na camada gold")
        
        # Salvando agregação por localização
        location_output_path = os.path.join(gold_path, "breweries_by_location")
        logger.info(f"Salvando agregação por localização em {location_output_path}")
        location_agg.coalesce(1).write.mode("overwrite").parquet(location_output_path)
        
        # Salvando agregação por tipo
        type_output_path = os.path.join(gold_path, "breweries_by_type")
        logger.info(f"Salvando agregação por tipo em {type_output_path}")
        type_agg.coalesce(1).write.mode("overwrite").parquet(type_output_path)
        
        # Salvando agregação combinada
        combined_output_path = os.path.join(gold_path, "breweries_by_type_location")
        logger.info(f"Salvando agregação combinada em {combined_output_path}")
        combined_agg.coalesce(1).write.mode("overwrite").parquet(combined_output_path)
        
        logger.info("Transformação gold concluída com sucesso")
        
    except FileNotFoundError as e:
        logger.error(f"Erro de arquivo não encontrado: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Erro de valor: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Erro não esperado: {str(e)}")
        raise
    finally:
        logger.info("Encerrando sessão Spark")
        spark.stop()

if __name__ == "__main__":
    try:
        run_gold_transformation()
    except Exception as e:
        logger.error(f"Falha na execução: {str(e)}")
        # Retorna código de erro para o Airflow saber que falhou
        exit(1)