from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    title = Column(String, nullable=True)
    publisher = Column(String, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(String, default="PENDING")

    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    facts = relationship("Evidence", back_populates="document", cascade="all, delete-orphan")

class DocumentPage(Base):
    __tablename__ = "document_pages"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    page_number = Column(Integer)
    text = Column(Text)

    document = relationship("Document", back_populates="pages")
    chunks = relationship("Chunk", back_populates="page", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="page", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    page_id = Column(Integer, ForeignKey("document_pages.id"), nullable=True)
    chunk_index = Column(Integer)
    text = Column(Text)
    embedding = Column(Vector(384)) # Assuming 384 dimensions for all-MiniLM-L6-v2

    document = relationship("Document", back_populates="chunks")
    page = relationship("DocumentPage", back_populates="chunks")
    evidence = relationship("Evidence", back_populates="chunk", cascade="all, delete-orphan")

class Fact(Base):
    __tablename__ = "facts"
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, index=True)
    predicate = Column(String)
    
    # Raw values
    raw_value = Column(String)
    raw_unit = Column(String)
    
    # Normalized values
    normalized_numeric_value = Column(Float, nullable=True)
    normalized_scale = Column(String, nullable=True)
    normalized_currency = Column(String, nullable=True)
    sign_convention_applied = Column(String, nullable=True)
    
    time_context = Column(String, nullable=True)
    scope = Column(String, nullable=True)
    geography = Column(String, nullable=True)
    qualifiers = Column(String, nullable=True)
    confidence = Column(Float, default=1.0)
    status = Column(String, default="ACTIVE")
    embedding = Column(Vector(384), nullable=True)

    evidence_links = relationship("Evidence", back_populates="fact", cascade="all, delete-orphan")
    relationships_a = relationship("Relationship", foreign_keys="[Relationship.fact_a_id]", back_populates="fact_a")
    relationships_b = relationship("Relationship", foreign_keys="[Relationship.fact_b_id]", back_populates="fact_b")

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True, index=True)
    fact_id = Column(Integer, ForeignKey("facts.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    page_id = Column(Integer, ForeignKey("document_pages.id"), nullable=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=True)
    evidence_text = Column(Text)

    fact = relationship("Fact", back_populates="evidence_links")
    document = relationship("Document", back_populates="facts")
    page = relationship("DocumentPage", back_populates="evidence")
    chunk = relationship("Chunk", back_populates="evidence")

class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(Integer, primary_key=True, index=True)
    fact_a_id = Column(Integer, ForeignKey("facts.id"))
    fact_b_id = Column(Integer, ForeignKey("facts.id"))
    relationship_type = Column(String) # CORROBORATES, CONTRADICTS, RECONCILES
    confidence = Column(Float)
    explanation = Column(Text)

    fact_a = relationship("Fact", foreign_keys=[fact_a_id], back_populates="relationships_a")
    fact_b = relationship("Fact", foreign_keys=[fact_b_id], back_populates="relationships_b")
