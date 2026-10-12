# API REST – Baozi Store

API da disciplina Desenvolvimento Web Back-End para controlar clientes, produtos e pedidos da Baozi Store.

## Tecnologias

- Java 21
- Spring Boot
- Spring Data JPA
- Banco relacional H2 (padrão). MySQL também está configurado no perfil `mysql`
- JSON

## Como executar

Pré-requisitos: JDK 21 e Maven.

```bash
mvn spring-boot:run
```

A API sobe em `http://localhost:8080`.

O banco H2 fica no arquivo `data/baozistore`. O console do H2 fica em `http://localhost:8080/h2-console`.

- JDBC URL: `jdbc:h2:file:./data/baozistore`
- Usuário: `sa`
- Senha: em branco

### MySQL (opcional)

Crie o acesso local com usuário `root` e senha `root`, ou ajuste `src/main/resources/application-mysql.properties`. Depois execute:

```bash
mvn spring-boot:run -Dspring-boot.run.profiles=mysql
```

## Endpoints

| Método | URL | Ação |
| --- | --- | --- |
| POST | /clientes | Cadastrar cliente |
| GET | /clientes | Listar clientes |
| GET | /clientes/{id} | Consultar cliente |
| PUT | /clientes/{id} | Atualizar cliente |
| DELETE | /clientes/{id} | Apagar cliente |
| POST | /produtos | Cadastrar produto |
| GET | /produtos | Listar produtos |
| GET | /produtos/{id} | Consultar produto |
| PUT | /produtos/{id} | Atualizar produto |
| DELETE | /produtos/{id} | Apagar produto |
| POST | /pedidos | Registrar pedido |
| GET | /pedidos | Listar pedidos |
| GET | /pedidos/{id} | Consultar pedido |
| PUT | /pedidos/{id} | Atualizar pedido |
| DELETE | /pedidos/{id} | Apagar pedido |

### Exemplos de JSON

Cliente:

```json
{
  "nome": "Lucas5172485",
  "clienteDesde": "2026-10-11"
}
```

Produto:

```json
{
  "nome": "Baozi de Churrasco",
  "preco": 12.90,
  "estoque": true
}
```

Pedido:

```json
{
  "clienteId": 1,
  "produtoId": 1,
  "quantidade": 8
}
```

A coleção do Postman está em `postman/Baozi-Store.postman_collection.json`.
