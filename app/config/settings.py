import os
import json
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from app.utils.common import get_project_meta, get_project_base_directory


# 定义全局配置常量
_meta = get_project_meta()
APP_NAME = _meta["name"]
APP_VERSION = _meta["version"]
APP_DESCRIPTION = _meta["description"]

PROJECT_BASE_DIR = get_project_base_directory()

class Settings(BaseSettings):
    """应用配置类 - 平铺结构"""
    
    # 应用基础配置
    service_host: str = Field(default="0.0.0.0", description="服务主机地址", env="SERVICE_HOST")
    service_port: int = Field(default=8000, description="服务端口", env="SERVICE_PORT")
    debug: bool = Field(default=False, description="调试模式", env="DEBUG")
    app_log_level: str = Field(default="INFO", description="日志级别", env="APP_LOG_LEVEL")

    # 认证配置
    auth_user_service_url: str = Field(default="http://localhost:8000", description="User-Service地址", env="AUTH_USER_SERVICE_URL")
    auth_request_timeout: int = Field(default=5, description="请求超时时间(秒)", env="AUTH_REQUEST_TIMEOUT")
    auth_jwks_endpoint: str = Field(default="/.well-known/jwks.json", description="JWKS端点", env="AUTH_JWKS_ENDPOINT")
    auth_jwt_config_endpoint: str = Field(default="/jwt-config", description="JWT配置端点", env="AUTH_JWT_CONFIG_ENDPOINT")
    auth_blacklist_endpoint: str = Field(default="/blacklist", description="黑名单端点", env="AUTH_BLACKLIST_ENDPOINT")
    
    # 数据库配置
    database_type: str = Field(default="postgresql", description="数据库类型: postgresql 或 mysql", env="DATABASE_TYPE")
    db_name: str = Field(default="knowledge_service", description="数据库名称", env="DB_NAME")
    db_pool_size: int = Field(default=10, description="连接池大小", env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, description="最大溢出连接数", env="DB_MAX_OVERFLOW")
    
    # PostgreSQL 配置
    postgresql_host: str = Field(default="localhost", description="PostgreSQL主机地址", env="POSTGRESQL_HOST")
    postgresql_port: int = Field(default=5432, description="PostgreSQL端口", env="POSTGRESQL_PORT")
    postgresql_user: str = Field(default="postgres", description="PostgreSQL用户名", env="POSTGRESQL_USER")
    postgresql_password: str = Field(default="your_password", description="PostgreSQL密码", env="POSTGRESQL_PASSWORD")
    
    # MySQL 配置
    mysql_host: str = Field(default="localhost", description="MySQL主机地址", env="MYSQL_HOST")
    mysql_port: int = Field(default=3306, description="MySQL端口", env="MYSQL_PORT")
    mysql_user: str = Field(default="root", description="MySQL用户名", env="MYSQL_USER")
    mysql_password: str = Field(default="your_password", description="MySQL密码", env="MYSQL_PASSWORD")
    
    # 文件存储配置
    storage_type: str = Field(default="minio", description="存储类型: minio, s3, local", env="STORAGE_TYPE")
    
    # MinIO 配置
    minio_endpoint: str = Field(default="localhost:9000", description="MinIO端点", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", description="MinIO访问密钥", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", description="MinIO秘密密钥", env="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, description="MinIO是否使用HTTPS", env="MINIO_SECURE")
    
    # S3 配置
    s3_region: str = Field(default="us-east-1", description="S3区域", env="S3_REGION")
    s3_endpoint_url: str = Field(default="https://your-s3-endpoint.com", description="S3端点URL", env="S3_ENDPOINT_URL")
    s3_access_key_id: str = Field(default="your_access_key", description="S3访问密钥ID", env="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str = Field(default="your_secret_key", description="S3秘密访问密钥", env="S3_SECRET_ACCESS_KEY")
    s3_use_ssl: bool = Field(default=True, description="S3是否使用SSL", env="S3_USE_SSL")

    # 本地存储配置
    local_upload_dir: str = Field(default="./uploads", description="本地上传目录", env="LOCAL_UPLOAD_DIR")
    
    # Azure Blob Storage SAS配置
    azure_account_url: str = Field(default="https://yourstorageaccount.blob.core.windows.net", description="Azure存储账户URL", env="AZURE_ACCOUNT_URL")
    azure_sas_token: str = Field(default="your_sas_token", description="Azure SAS令牌", env="AZURE_SAS_TOKEN")
    
    # Azure Blob Storage SPN配置
    azure_spn_account_url: str = Field(default="https://yourstorageaccount.dfs.core.windows.net", description="Azure SPN存储账户URL", env="AZURE_SPN_ACCOUNT_URL")
    azure_spn_client_id: str = Field(default="your_client_id", description="Azure SPN客户端ID", env="AZURE_SPN_CLIENT_ID")
    azure_spn_client_secret: str = Field(default="your_client_secret", description="Azure SPN客户端密钥", env="AZURE_SPN_CLIENT_SECRET")
    azure_spn_tenant_id: str = Field(default="your_tenant_id", description="Azure SPN租户ID", env="AZURE_SPN_TENANT_ID")
    azure_spn_container_name: str = Field(default="your_container", description="Azure SPN容器名称", env="AZURE_SPN_CONTAINER_NAME")
    
    # OSS配置
    oss_access_key: str = Field(default="your_access_key", description="OSS访问密钥ID", env="OSS_ACCESS_KEY")
    oss_secret_key: str = Field(default="your_secret_key", description="OSS秘密访问密钥", env="OSS_SECRET_KEY")
    oss_endpoint_url: str = Field(default="https://oss-cn-hangzhou.aliyuncs.com", description="OSS端点URL", env="OSS_ENDPOINT_URL")
    oss_region: str = Field(default="cn-hangzhou", description="OSS区域", env="OSS_REGION")
    oss_prefix_path: str = Field(default="", description="OSS前缀路径", env="OSS_PREFIX_PATH")
    
    # Redis配置
    redis_host: str = Field(default="localhost", description="Redis主机地址", env="REDIS_HOST")
    redis_port: int = Field(default=6379, description="Redis端口", env="REDIS_PORT")
    redis_db: int = Field(default=0, description="Redis数据库编号", env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, description="Redis密码", env="REDIS_PASSWORD")
    redis_ssl: bool = Field(default=False, description="是否使用SSL连接", env="REDIS_SSL")
    redis_decode_responses: bool = Field(default=True, description="是否自动解码响应", env="REDIS_DECODE_RESPONSES")
    redis_socket_connect_timeout: int = Field(default=5, description="连接超时时间(秒)", env="REDIS_SOCKET_CONNECT_TIMEOUT")
    redis_socket_timeout: int = Field(default=5, description="读写超时时间(秒)", env="REDIS_SOCKET_TIMEOUT")
    redis_retry_on_timeout: bool = Field(default=True, description="超时时是否重试", env="REDIS_RETRY_ON_TIMEOUT")
    redis_max_connections: int = Field(default=5, description="每个数据库的最大连接数", env="REDIS_MAX_CONNECTIONS")


    # =============================================================================
    # 向量存储配置 - Vector Store
    # =============================================================================
    # 向量存储引擎类型 (elasticsearch, opensearch)
    vector_store_engine: str = Field(default="elasticsearch", description="向量存储引擎类型", env="VECTOR_STORE_ENGINE")
    # 向量存储映射文件名称
    vector_store_mapping: str = Field(default="es_doc_mapping.json", description="向量存储映射文件名称", env="VECTOR_STORE_MAPPING")
    
    # Elasticsearch配置
    es_hosts: str = Field(default="https://localhost:9200", description="Elasticsearch主机地址", env="ES_HOSTS")
    es_username: str = Field(default="elastic", description="Elasticsearch用户名", env="ES_USERNAME")
    es_password: str = Field(default="changeme", description="Elasticsearch密码", env="ES_PASSWORD")
    
    # OpenSearch配置
    os_hosts: str = Field(default="http://localhost:9200", description="OpenSearch主机地址", env="OS_HOSTS")
    os_username: str = Field(default="admin", description="OpenSearch用户名", env="OS_USERNAME")
    os_password: str = Field(default="admin", description="OpenSearch密码", env="OS_PASSWORD")
    
    # =============================================================================
    # 模型配置说明 见：app/config/xxx.json
    # =============================================================================

    # =============================================================================
    # 业务配置 - Business Configuration
    # =============================================================================
    # GitHub配置
    github_client_id: str = Field(default="your-github-client-id", description="GitHub客户端ID", env="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="your-github-client-secret", description="GitHub客户端密钥", env="GITHUB_CLIENT_SECRET")
    github_token: str = Field(default="your-github-token", description="GitHub访问令牌", env="GITHUB_TOKEN")
    
    # Gitee配置
    gitee_client_id: str = Field(default="your-gitee-client-id", description="Gitee客户端ID", env="GITEE_CLIENT_ID")
    gitee_client_secret: str = Field(default="your-gitee-client-secret", description="Gitee客户端密钥", env="GITEE_CLIENT_SECRET")
    gitee_token: str = Field(default="your-gitee-token", description="Gitee访问令牌", env="GITEE_TOKEN")
    
    # Git配置
    git_path: str = Field(default="./repositories", description="Git仓库存储路径", env="GIT_PATH")
    git_username: str = Field(default="your-git-username", description="Git用户名", env="GIT_USERNAME")
    git_password: str = Field(default="your-git-password", description="Git密码", env="GIT_PASSWORD")
    git_email: str = Field(default="koalawiki@example.com", description="Git邮箱", env="GIT_EMAIL")
    
    # Mem0配置
    mem0_enable_mem0: bool = Field(default=False, description="是否启用Mem0", env="MEM0_ENABLE_MEM0")
    mem0_api_key: str = Field(default="your-mem0-api-key", description="Mem0 API密钥", env="MEM0_MEM0_API_KEY")
    mem0_endpoint: str = Field(default="https://api.mem0.ai", description="Mem0端点", env="MEM0_MEM0_ENDPOINT")
    
    # REPOWIKI文档配置
    repowik_enable_code_dependency_analysis: bool = Field(default=True, description="是否启用代码依赖分析", env="REPOWIK_ENABLE_CODE_DEPENDENCY_ANALYSIS")
    repowik_enable_incremental_update: bool = Field(default=True, description="是否启用增量更新", env="REPOWIK_ENABLE_INCREMENTAL_UPDATE")
    repowik_enable_smart_filter: bool = Field(default=True, description="是否启用智能过滤", env="REPOWIK_ENABLE_SMART_FILTER")
    repowik_catalogue_format: str = Field(default="compact", description="目录格式", env="REPOWIK_CATALOGUE_FORMAT")
    repowik_enable_warehouse_function_prompt_task: bool = Field(default=True, description="是否启用仓库函数提示任务", env="REPOWIK_ENABLE_WAREHOUSE_FUNCTION_PROMPT_TASK")
    repowik_enable_warehouse_description_task: bool = Field(default=True, description="是否启用仓库描述任务", env="REPOWIK_ENABLE_WAREHOUSE_DESCRIPTION_TASK")
    repowik_enable_file_commit: bool = Field(default=True, description="是否启用文件提交", env="REPOWIK_ENABLE_FILE_COMMIT")
    repowik_enable_warehouse_commit: bool = Field(default=True, description="是否启用仓库提交", env="REPOWIK_ENABLE_WAREHOUSE_COMMIT")
    repowik_refine_and_enhance_quality: bool = Field(default=True, description="是否优化和提升质量", env="REPOWIK_REFINE_AND_ENHANCE_QUALITY")
    repowik_enable_code_compression: bool = Field(default=False, description="是否启用代码压缩", env="REPOWIK_ENABLE_CODE_COMPRESSION")
    repowik_excluded_files: str = Field(default='["*.log", "*.tmp", "node_modules"]', description="排除的文件列表(JSON格式)", env="REPOWIK_EXCLUDED_FILES")
    repowik_excluded_folders: str = Field(default='["node_modules", ".git", "dist"]', description="排除的文件夹列表(JSON格式)", env="REPOWIK_EXCLUDED_FOLDERS")
    repowik_git_path: str = Field(default="./repositories", description="REPOWIKI Git路径", env="REPOWIK_GIT_PATH")

    # =============================================================================
    # 仓库管理配置 - Repository Management
    # =============================================================================
    repo_storage_path: str = Field(default="./repos", description="代码仓存储路径", env="REPO_STORAGE_PATH")
    enable_code_dependency_analysis: bool = Field(default=False, description="是否启用代码依赖分析", env="ENABLE_CODE_DEPENDENCY_ANALYSIS")
    
    class Config:
        env_file = "env"
        env_file_encoding = "utf-8"
    
    @property
    def database_url(self) -> str:
        """生成数据库连接URL"""
        if self.database_type.lower() == "postgresql":
            return f"postgresql+asyncpg://{self.postgresql_user}:{self.postgresql_password}@{self.postgresql_host}:{self.postgresql_port}/{self.db_name}"
        elif self.database_type.lower() == "mysql":
            return f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.db_name}"
        else:
            return "sqlite+aiosqlite:///./koalawiki.db"
    
    @field_validator('repowik_excluded_files', 'repowik_excluded_folders')
    @classmethod
    def validate_json_list(cls, v):
        """验证JSON格式的列表配置"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v
    
    @property
    def redis_url(self) -> str:
        """生成Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def repowik_excluded_files_list(self) -> List[str]:
        """获取排除文件列表"""
        if isinstance(self.repowik_excluded_files, str):
            try:
                return json.loads(self.repowik_excluded_files)
            except json.JSONDecodeError:
                return []
        return self.repowik_excluded_files
    
    @property
    def repowik_excluded_folders_list(self) -> List[str]:
        """获取排除文件夹列表"""
        if isinstance(self.repowik_excluded_folders, str):
            try:
                return json.loads(self.repowik_excluded_folders)
            except json.JSONDecodeError:
                return []
        return self.repowik_excluded_folders


# 全局配置实例
settings = Settings() 