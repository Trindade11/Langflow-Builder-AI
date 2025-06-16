from typing import List, Dict, Any
from langflow.custom import Component
from langflow.inputs import (
    HandleInput,
    IntInput,
    FloatInput,
    MultilineInput,
)
from langflow.schema import Data
from langflow.template import Output

class LLMRerankComponent(Component):
    display_name = "LLM Rerank (Lexical + Semântico + Pesos)"
    icon = "Sort"
    description = "Rerank de chunks combinando resultados lexicais e semânticos usando um modelo LLM e pesos dinâmicos."

    inputs = [
        HandleInput(
            name="question",
            display_name="Pergunta",
            input_types=["str", "Message"],
            required=True,
        ),
        HandleInput(
            name="rerank_pesos",
            display_name="Rerank Pesos",
            input_types=["dict", "Data", "str"],
            required=True,
        ),
        HandleInput(
            name="lexical_chunks",
            display_name="Chunks Lexicais",
            input_types=["list", "Data"],
            required=True,
        ),
        HandleInput(
            name="semantic_chunks",
            display_name="Chunks Semânticos",
            input_types=["list", "Data"],
            required=True,
        ),
        HandleInput(
            name="llm",
            display_name="LLM Model",
            input_types=["LanguageModel"],
            required=True,
        ),
        IntInput(
            name="top_k",
            display_name="Top K",
            value=5,
            info="Número máximo de chunks rerankeados a retornar.",
            required=False,
        ),
        MultilineInput(
            name="score_final_min",
            display_name="Score Final Mínimo",
            value="2.0",
            info="Apenas chunks com rerank_score_final maior ou igual a este valor (de 0 a 5) serão retornados.",
            required=False,
        ),
    ]

    outputs = [
        Output(
            name="reranked_chunks",
            display_name="Chunks Rerankeados",
            method="rerank_chunks",
        ),
    ]

    def _extract_chunks(self, input_data):
        if input_data is None:
            return []
        if isinstance(input_data, Data):
            data = getattr(input_data, "data", None)
            if isinstance(data, dict) and "results" in data:
                return data["results"]
            if isinstance(data, dict) and "reranked" in data:
                return data["reranked"]
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return list(data.values())
            return []
        if isinstance(input_data, dict):
            if "results" in input_data:
                return input_data["results"]
            if "reranked" in input_data:
                return input_data["reranked"]
            return list(input_data.values())
        if isinstance(input_data, list):
            return input_data
        return []

    def _chunk_to_dict(self, chunk):
        if isinstance(chunk, Data):
            if hasattr(chunk, "data"):
                return dict(chunk.data) if isinstance(chunk.data, dict) else {"data": chunk.data}
            return {"data": chunk}
        return dict(chunk) if not isinstance(chunk, dict) else chunk

    def _call_llm(self, llm, prompt):
        try:
            return llm(prompt)
        except Exception:
            try:
                return llm.invoke(prompt)
            except Exception:
                try:
                    return llm.predict(prompt)
                except Exception:
                    return "0"

    def _parse_pesos(self, pesos_input):
        import json
        if isinstance(pesos_input, dict):
            return pesos_input
        if isinstance(pesos_input, Data):
            data = getattr(pesos_input, "data", None)
            if isinstance(data, dict):
                return data
            if isinstance(data, str):
                try:
                    return json.loads(data)
                except Exception:
                    return {}
        if isinstance(pesos_input, str):
            try:
                return json.loads(pesos_input)
            except Exception:
                return {}
        return {}

    def _parse_score_final_min(self, value):
        try:
            return float(str(value).replace(",", "."))
        except Exception:
            return 2.0

    def rerank_chunks(self) -> Data:
        import re
        question = self.question.text if hasattr(self.question, 'text') else str(self.question)
        pesos = self._parse_pesos(self.rerank_pesos)
        lex_chunks = self._extract_chunks(self.lexical_chunks)
        sem_chunks = self._extract_chunks(self.semantic_chunks)
        llm = self.llm
        top_k = self.top_k if hasattr(self, 'top_k') else 5
        score_final_min = self._parse_score_final_min(getattr(self, 'score_final_min', 2.0))

        peso_lexical = float(pesos.get('lexical', 0.5))
        peso_semantic = float(pesos.get('semantic', 0.5))

        # Junta e remove duplicados por _id
        all_chunks = {}
        for chunk in (lex_chunks or []):
            chunk = self._chunk_to_dict(chunk)
            _id = str(chunk.get('_id', id(chunk)))
            chunk['source'] = 'lexical'
            all_chunks[_id] = chunk
        for chunk in (sem_chunks or []):
            chunk = self._chunk_to_dict(chunk)
            _id = str(chunk.get('_id', id(chunk)))
            chunk['source'] = 'semantic'
            all_chunks[_id] = chunk
        chunks = list(all_chunks.values())

        if not isinstance(chunks, list) or not chunks:
            self.status = "Nenhum chunk de entrada válido"
            return Data(data={"reranked": []})

        # Prompt único para batch, agora incluindo a pergunta
        prompt = f"Pergunta: {question}\nAvalie de 0 a 10 o quanto cada texto abaixo responde à pergunta. Responda apenas com uma lista de números, na mesma ordem dos textos.\n"
        for idx, chunk in enumerate(chunks):
            text = chunk.get('text', '') or chunk.get('page_content', '')
            prompt += f"\nTexto {idx+1}: {text}"

        score_str = self._call_llm(llm, prompt)
        print(f"Prompt enviado ao LLM:\n{prompt}")
        print(f"Resposta bruta do LLM: {score_str}")

        # Extrai lista de scores
        scores = re.findall(r"[-+]?[0-9]*\.?[0-9]+", str(score_str))
        scores = [float(s.replace(',', '.')) for s in scores][:len(chunks)]

        # Atribui scores aos chunks e calcula score final com pesos
        reranked = []
        for chunk, score in zip(chunks, scores):
            chunk['rerank_score_llm'] = score
            # Score lexical e semântico (se existirem)
            score_lexical = float(chunk.get('score', 0)) if chunk.get('source') == 'lexical' else 0.0
            score_semantic = float(chunk.get('similarity_score', 0)) if chunk.get('source') == 'semantic' else 0.0
            # Score final ponderado
            chunk['rerank_score_final'] = (
                peso_lexical * score_lexical + peso_semantic * score_semantic + score
            ) / (1 + peso_lexical + peso_semantic)
            reranked.append(chunk)

        # Filtra apenas os chunks com score LLM > 0
        reranked = [chunk for chunk in reranked if chunk.get('rerank_score_llm', 0) > 0]
        # Filtra pelo score final mínimo
        reranked = [chunk for chunk in reranked if chunk.get('rerank_score_final', 0) >= score_final_min]

        reranked.sort(key=lambda x: x['rerank_score_final'], reverse=True)
        reranked = reranked[:top_k]
        self.status = f"Rerank finalizado. Top {len(reranked)} retornados (score final >= {score_final_min})."
        return Data(data={"reranked": reranked})
