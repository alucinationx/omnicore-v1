# OmniCore AI - Sistema de Processamento de Documentos com IA
# Análise, OCR, extração de dados e classificação de documentos empresariais

import asyncio
import logging
import tempfile
import os
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import re
from abc import ABC, abstractmethod

# Bibliotecas para processamento de documentos
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import fitz  # PyMuPDF
import docx2txt
import pandas as pd
from openpyxl import load_workbook
import easyocr

# IA e NLP
import openai
from transformers import pipeline, AutoTokenizer, AutoModel
import spacy
from sentence_transformers import SentenceTransformer

# Logging
logger = logging.getLogger("OmniCore.DocumentProcessor")

@dataclass
class DocumentMetadata:
    """Metadados do documento"""
    filename: str
    file_type: str
    file_size: int
    creation_date: Optional[datetime]
    modification_date: Optional[datetime]
    pages: int = 0
    language: str = "pt"
    encoding: str = "utf-8"

@dataclass
class ExtractedEntity:
    """Entidade extraída do documento"""
    type: str  # CPF, CNPJ, email, telefone, valor_monetario, data, etc.
    value: str
    confidence: float
    position: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height
    page: int = 0

@dataclass
class DocumentAnalysisResult:
    """Resultado da análise de documento"""
    document_id: str
    metadata: DocumentMetadata
    extracted_text: str
    entities: List[ExtractedEntity]
    classification: str
    confidence: float
    summary: str
    key_information: Dict[str, Any]
    processing_time: float
    errors: List[str] = field(default_factory=list)

class DocumentProcessor:
    """Processador principal de documentos"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ocr_engine = None
        self.nlp_model = None
        self.embedding_model = None
        self.entity_extractor = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Inicializa modelos de IA"""
        try:
            # Configurar OCR
            if self.config.get("ocr_engine") == "easyocr":
                self.ocr_engine = easyocr.Reader(['pt', 'en'])
            else:
                # Tesseract como padrão
                pytesseract.pytesseract.tesseract_cmd = self.config.get(
                    "tesseract_path", "/usr/bin/tesseract"
                )
            
            # Modelo de NLP para português
            try:
                self.nlp_model = spacy.load("pt_core_news_sm")
            except OSError:
                logger.warning("Modelo spaCy pt não encontrado, usando modelo básico")
                self.nlp_model = None
            
            # Modelo de embeddings
            self.embedding_model = SentenceTransformer('neuralmind/bert-base-portuguese-cased')
            
            # Pipeline de classificação
            self.entity_extractor = pipeline(
                "ner",
                model="neuralmind/bert-base-portuguese-cased",
                aggregation_strategy="simple"
            )
            
            logger.info("Modelos de IA inicializados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar modelos: {str(e)}")
    
    async def process_document(self, 
                             file_path: str, 
                             analysis_type: str = "complete",
                             options: Dict[str, Any] = None) -> DocumentAnalysisResult:
        """
        Processa documento com análise completa
        
        Args:
            file_path: Caminho para o arquivo
            analysis_type: Tipo de análise (complete, ocr_only, extract_only, classify_only)
            options: Opções adicionais de processamento
        """
        start_time = datetime.now()
        options = options or {}
        
        try:
            # Gerar ID único para o documento
            document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Extrair metadados
            metadata = self._extract_metadata(file_path)
            
            # Extrair texto baseado no tipo de arquivo
            extracted_text = await self._extract_text(file_path, metadata.file_type)
            
            # Análise baseada no tipo solicitado
            entities = []
            classification = "unknown"
            confidence = 0.0
            summary = ""
            key_information = {}
            
            if analysis_type in ["complete", "extract_only"]:
                entities = await self._extract_entities(extracted_text)
            
            if analysis_type in ["complete", "classify_only"]:
                classification, confidence = await self._classify_document(extracted_text, entities)
            
            if analysis_type == "complete":
                summary = await self._generate_summary(extracted_text)
                key_information = await self._extract_key_information(
                    extracted_text, entities, classification
                )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return DocumentAnalysisResult(
                document_id=document_id,
                metadata=metadata,
                extracted_text=extracted_text,
                entities=entities,
                classification=classification,
                confidence=confidence,
                summary=summary,
                key_information=key_information,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Erro no processamento do documento: {str(e)}")
            raise
    
    def _extract_metadata(self, file_path: str) -> DocumentMetadata:
        """Extrai metadados do arquivo"""
        path_obj = Path(file_path)
        stat = path_obj.stat()
        
        file_type = path_obj.suffix.lower()
        pages = 0
        
        # Contar páginas baseado no tipo de arquivo
        if file_type == ".pdf":
            try:
                doc = fitz.open(file_path)
                pages = len(doc)
                doc.close()
            except:
                pages = 0
        
        return DocumentMetadata(
            filename=path_obj.name,
            file_type=file_type,
            file_size=stat.st_size,
            creation_date=datetime.fromtimestamp(stat.st_ctime),
            modification_date=datetime.fromtimestamp(stat.st_mtime),
            pages=pages
        )
    
    async def _extract_text(self, file_path: str, file_type: str) -> str:
        """Extrai texto do arquivo baseado no tipo"""
        try:
            if file_type == ".pdf":
                return await self._extract_text_from_pdf(file_path)
            elif file_type in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
                return await self._extract_text_from_image(file_path)
            elif file_type in [".docx", ".doc"]:
                return await self._extract_text_from_docx(file_path)
            elif file_type in [".xlsx", ".xls"]:
                return await self._extract_text_from_excel(file_path)
            elif file_type == ".txt":
                return await self._extract_text_from_txt(file_path)
            else:
                raise ValueError(f"Tipo de arquivo não suportado: {file_type}")
                
        except Exception as e:
            logger.error(f"Erro na extração de texto: {str(e)}")
            return ""
    
    async def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extrai texto de PDF com OCR quando necessário"""
        text_parts = []
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Tentar extrair texto diretamente
                text = page.get_text()
                
                # Se pouco texto foi extraído, usar OCR
                if len(text.strip()) < 50:
                    # Converter página para imagem
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
                    img_data = pix.tobytes("png")
                    
                    # Salvar temporariamente e processar com OCR
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                        temp_file.write(img_data)
                        temp_path = temp_file.name
                    
                    try:
                        ocr_text = await self._extract_text_from_image(temp_path)
                        text = ocr_text if len(ocr_text) > len(text) else text
                    finally:
                        os.unlink(temp_path)
                
                text_parts.append(f"--- Página {page_num + 1} ---\n{text}\n")
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Erro ao processar PDF: {str(e)}")
            return ""
        
        return "\n".join(text_parts)
    
    async def _extract_text_from_image(self, file_path: str) -> str:
        """Extrai texto de imagem usando OCR"""
        try:
            # Pré-processamento da imagem
            processed_image = self._preprocess_image(file_path)
            
            if self.ocr_engine and hasattr(self.ocr_engine, 'readtext'):
                # EasyOCR
                results = self.ocr_engine.readtext(processed_image)
                text = " ".join([result[1] for result in results])
            else:
                # Tesseract
                # Configuração otimizada para documentos em português
                custom_config = r'--oem 3 --psm 6 -l por'
                text = pytesseract.image_to_string(
                    processed_image, 
                    config=custom_config
                )
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Erro no OCR: {str(e)}")
            return ""
    
    def _preprocess_image(self, file_path: str) -> Image.Image:
        """Pré-processa imagem para melhorar OCR"""
        try:
            # Carregar imagem
            image = Image.open(file_path)
            
            # Converter para escala de cinza
            if image.mode != 'L':
                image = image.convert('L')
            
            # Redimensionar se muito pequena
            width, height = image.size
            if width < 1000 or height < 1000:
                factor = max(1000/width, 1000/height)
                new_size = (int(width * factor), int(height * factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Melhorar contraste
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Aplicar filtro para reduzir ruído
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
            
        except Exception as e:
            logger.error(f"Erro no pré-processamento: {str(e)}")
            return Image.open(file_path)
    
    async def _extract_text_from_docx(self, file_path: str) -> str:
        """Extrai texto de arquivo DOCX"""
        try:
            text = docx2txt.process(file_path)
            return text.strip()
        except Exception as e:
            logger.error(f"Erro ao processar DOCX: {str(e)}")
            return ""
    
    async def _extract_text_from_excel(self, file_path: str) -> str:
        """Extrai texto de arquivo Excel"""
        try:
            # Ler todas as planilhas
            xl_file = pd.ExcelFile(file_path)
            text_parts = []
            
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Converter DataFrame para texto
                sheet_text = f"--- Planilha: {sheet_name} ---\n"
                sheet_text += df.to_string(index=False)
                text_parts.append(sheet_text)
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Erro ao processar Excel: {str(e)}")
            return ""
    
    async def _extract_text_from_txt(self, file_path: str) -> str:
        """Extrai texto de arquivo TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Tentar com encoding alternativo
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"Erro ao ler arquivo TXT: {str(e)}")
                return ""
    
    async def _extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extrai entidades nomeadas do texto"""
        entities = []
        
        try:
            # Extração com regex para entidades brasileiras específicas
            regex_entities = self._extract_brazilian_entities(text)
            entities.extend(regex_entities)
            
            # Extração com modelo de NLP se disponível
            if self.entity_extractor:
                try:
                    nlp_entities = self.entity_extractor(text)
                    for ent in nlp_entities:
                        entities.append(ExtractedEntity(
                            type=ent['entity_group'],
                            value=ent['word'],
                            confidence=ent['score']
                        ))
                except Exception as e:
                    logger.warning(f"Erro na extração NLP: {str(e)}")
            
            # Remover duplicatas
            entities = self._remove_duplicate_entities(entities)
            
        except Exception as e:
            logger.error(f"Erro na extração de entidades: {str(e)}")
        
        return entities
    
    def _extract_brazilian_entities(self, text: str) -> List[ExtractedEntity]:
        """Extrai entidades específicas do Brasil usando regex"""
        entities = []
        
        # Padrões regex para entidades brasileiras
        patterns = {
            "cpf": r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
            "cnpj": r'\b\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}\b',
            "cep": r'\b\d{5}-?\d{3}\b',
            "telefone": r'\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4,5}-?\d{4}\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "valor_monetario": r'R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?',
            "data": r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b',
            "numero_documento": r'\b\d{6,20}\b'
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(ExtractedEntity(
                    type=entity_type,
                    value=match.group(),
                    confidence=0.9,  # Alta confiança para regex
                    position=(match.start(), match.end(), 0, 0)
                ))
        
        return entities
    
    def _remove_duplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove entidades duplicadas"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            # Normalizar valor para comparação
            normalized_value = entity.value.lower().strip()
            key = (entity.type, normalized_value)
            
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    async def _classify_document(self, text: str, entities: List[ExtractedEntity]) -> Tuple[str, float]:
        """Classifica tipo de documento"""
        try:
            # Classificação baseada em keywords e entidades
            classification_rules = {
                "contrato": {
                    "keywords": ["contrato", "acordo", "partes", "cláusula", "vigência"],
                    "entities": ["cpf", "cnpj"],
                    "weight": 1.0
                },
                "nota_fiscal": {
                    "keywords": ["nota fiscal", "nf-e", "danfe", "imposto", "icms"],
                    "entities": ["cnpj", "valor_monetario"],
                    "weight": 1.0
                },
                "boleto": {
                    "keywords": ["boleto", "vencimento", "pagamento", "banco"],
                    "entities": ["valor_monetario", "data", "numero_documento"],
                    "weight": 1.0
                },
                "relatorio_financeiro": {
                    "keywords": ["relatório", "balanço", "receita", "despesa", "lucro"],
                    "entities": ["valor_monetario", "data"],
                    "weight": 0.8
                },
                "documento_identidade": {
                    "keywords": ["identidade", "rg", "cnh", "passaporte"],
                    "entities": ["cpf", "numero_documento"],
                    "weight": 0.9
                }
            }
            
            text_lower = text.lower()
            entity_types = {e.type for e in entities}
            
            scores = {}
            
            for doc_type, rules in classification_rules.items():
                score = 0.0
                
                # Pontuação por keywords
                keyword_score = sum(1 for keyword in rules["keywords"] if keyword in text_lower)
                keyword_score = min(keyword_score / len(rules["keywords"]), 1.0)
                
                # Pontuação por entidades
                entity_score = sum(1 for entity_type in rules["entities"] if entity_type in entity_types)
                entity_score = min(entity_score / len(rules["entities"]), 1.0)
                
                # Pontuação final
                score = (keyword_score + entity_score) / 2 * rules["weight"]
                scores[doc_type] = score
            
            # Selecionar classificação com maior pontuação
            if scores:
                best_classification = max(scores, key=scores.get)
                confidence = scores[best_classification]
                
                # Se confiança for muito baixa, classificar como genérico
                if confidence < 0.3:
                    return "documento_generico", confidence
                
                return best_classification, confidence
            
            return "documento_generico", 0.1
            
        except Exception as e:
            logger.error(f"Erro na classificação: {str(e)}")
            return "erro_classificacao", 0.0
    
    async def _generate_summary(self, text: str) -> str:
        """Gera resumo do documento"""
        try:
            # Limitar texto para resumo (primeiros 2000 caracteres)
            text_for_summary = text[:2000]
            
            # Se OpenAI estiver configurado, usar GPT
            if self.config.get("openai_api_key"):
                openai.api_key = self.config["openai_api_key"]
                
                prompt = f"""
                Analise o seguinte documento e gere um resumo conciso em português:
                
                {text_for_summary}
                
                Resumo:
                """
                
                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.3
                )
                
                return response.choices[0].message.content.strip()
            
            # Fallback: resumo simples baseado em primeiras frases
            sentences = text_for_summary.split('.')[:3]
            return '. '.join(sentences) + '.'
            
        except Exception as e:
            logger.error(f"Erro na geração de resumo: {str(e)}")
            return "Resumo não disponível."
    
    async def _extract_key_information(self, 
                                     text: str, 
                                     entities: List[ExtractedEntity],
                                     classification: str) -> Dict[str, Any]:
        """Extrai informações-chave baseadas no tipo de documento"""
        key_info = {
            "total_entities": len(entities),
            "entity_types": list(set(e.type for e in entities)),
            "document_length": len(text),
            "classification": classification
        }
        
        # Informações específicas por tipo de documento
        entity_dict = {e.type: [ent.value for ent in entities if ent.type == e.type] 
                      for e in entities}
        
        if classification == "contrato":
            key_info.update({
                "partes_envolvidas": entity_dict.get("cpf", []) + entity_dict.get("cnpj", []),
                "valores": entity_dict.get("valor_monetario", []),
                "datas": entity_dict.get("data", [])
            })
        
        elif classification == "nota_fiscal":
            key_info.update({
                "fornecedor_cnpj": entity_dict.get("cnpj", []),
                "valores": entity_dict.get("valor_monetario", []),
                "data_emissao": entity_dict.get("data", [])
            })
        
        elif classification == "boleto":
            key_info.update({
                "valor_boleto": entity_dict.get("valor_monetario", []),
                "data_vencimento": entity_dict.get("data", []),
                "codigo_barras": entity_dict.get("numero_documento", [])
            })
        
        return key_info

# Exemplo de uso
async def exemplo_processamento_documentos():
    """Exemplo de uso do processador de documentos"""
    
    config = {
        "ocr_engine": "tesseract",  # ou "easyocr"
        "tesseract_path": "/usr/bin/tesseract",
        "openai_api_key": "sua_chave_openai_aqui"
    }
    
    processor = DocumentProcessor(config)
    
    # Processar um documento PDF
    resultado = await processor.process_document(
        "contrato_exemplo.pdf",
        analysis_type="complete"
    )
    
    print(f"Documento processado: {resultado.document_id}")
    print(f"Classificação: {resultado.classification} (confiança: {resultado.confidence:.2f})")
    print(f"Entidades encontradas: {len(resultado.entities)}")
    print(f"Resumo: {resultado.summary}")
    print(f"Tempo de processamento: {resultado.processing_time:.2f}s")
    
    # Mostrar entidades encontradas
    for entity in resultado.entities:
        print(f"- {entity.type}: {entity.value} (confiança: {entity.confidence:.2f})")

if __name__ == "__main__":
    asyncio.run(exemplo_processamento_documentos())