# Escalador TCM — Streamlit + Supabase

Este pacote cria um site para editar:

- Servidores e habilitações;
- Ausências, férias, abonos, Juri, OTC, Lic.Médica, Folga TRE e substituição de chefia do Gil;
- Feriados/dias sem expediente;
- Escala mensal e exportação em Excel.

## 1. Criar o banco no Supabase

1. Crie um projeto no Supabase.
2. Abra **SQL Editor**.
3. Cole e rode o conteúdo de `supabase_schema.sql`.
4. Copie:
   - Project URL;
   - anon public key.

Para uma primeira versão por link, deixe RLS desativado nessas tabelas. Se precisar controle por login, dá para endurecer depois.

## 2. Subir o app no Streamlit Cloud

1. Crie um repositório no GitHub.
2. Envie estes arquivos:
   - `streamlit_app.py`
   - `requirements.txt`
   - `supabase_schema.sql`
3. No Streamlit Cloud, crie um app novo apontando para `streamlit_app.py`.
4. Em **Secrets**, coloque:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "SUA-ANON-KEY"
```

5. Salve e reinicie o app.

## 3. Primeiro uso

No menu lateral do app:

1. Clique em **Inicializar/atualizar dados padrão**.
2. Confira os servidores.
3. Alimente a aba **Ausências**.
4. Confira feriados.
5. Vá em **Gerar escala** e baixe o Excel.

## Regras implementadas

- Data fim é opcional; se vazia, vale a data início.
- Ausência de dia inteiro bloqueia DOC, Manhã e Tarde.
- Ausência Manhã/Tarde/DOC bloqueia só a atividade correspondente.
- Gil pode aparecer nas ausências.
- Substituto padrão do Gil é Bruno.
- Se Bruno também estiver ausente no período do Gil, o sistema considera **A definir**.
- Substituto definido do Gil é retirado da escala naquele período.
- Se faltarem três pessoas diferentes disponíveis no dia, o sistema aceita repetição como exceção, sem usar pessoa ausente ou não habilitada.

## Observação

Este app não usa macro, não precisa instalar Python no trabalho e salva os dados no Supabase, não no arquivo Excel local.
