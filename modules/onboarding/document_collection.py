import os
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from werkzeug.utils import secure_filename
from database.connection import get_db_session
from database.models import Document, Employee, OnboardingChecklist, DocumentType, EmployeeType
from modules.email.email_Sender import EmailSender
from config import config
from utils.helpers import is_valid_file_type, sanitize_filename, format_file_size

logger = logging.getLogger(__name__)

class DocumentCollector:
    """Handle document collection for employees"""
    
    def __init__(self):
        self.email_sender = EmailSender()
        self.upload_folder = config.UPLOAD_FOLDER
        
        # Create upload folder if it doesn't exist
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
    
    def get_required_documents(self, employee_type: str) -> List[str]:
        """Get list of required documents based on employee type"""
        return config.REQUIRED_DOCUMENTS.get(employee_type, [])
    
    def upload_document(self, employee_id: int, document_data: Dict[str, Any], 
                       file_data: Any) -> Dict[str, Any]:
        """Upload a document for an employee"""
        try:
            with get_db_session() as session:
                # Get employee
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Validate file type
                filename = file_data.name
                if not is_valid_file_type(filename, config.ALLOWED_EXTENSIONS):
                    return {
                        'success': False,
                        'message': f'Invalid file type. Allowed types: {", ".join(config.ALLOWED_EXTENSIONS)}'
                    }
                
                # Check file size
                file_size = len(file_data.getvalue())
                if file_size > config.MAX_FILE_SIZE:
                    return {
                        'success': False,
                        'message': f'File size exceeds limit of {format_file_size(config.MAX_FILE_SIZE)}'
                    }
                
                # Create employee folder
                employee_folder = os.path.join(
                    self.upload_folder, 
                    f"{employee.employee_id}_{sanitize_filename(employee.full_name)}"
                )
                if not os.path.exists(employee_folder):
                    os.makedirs(employee_folder)
                
                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = sanitize_filename(filename)
                unique_filename = f"{timestamp}_{safe_filename}"
                file_path = os.path.join(employee_folder, unique_filename)
                
                # Save file
                if config.USE_S3:
                    file_url = self._upload_to_s3(file_data, unique_filename, employee.employee_id)
                    if not file_url:
                        return {
                            'success': False,
                            'message': 'Failed to upload file to S3'
                        }
                    file_path = file_url
                else:
                    # Save locally
                    with open(file_path, 'wb') as f:
                        f.write(file_data.getvalue())
                
                # Determine document type
                doc_type = self._determine_document_type(document_data['document_name'])
                
                # Create document record
                document = Document(
                    employee_id=employee_id,
                    document_type=doc_type,
                    document_name=document_data['document_name'],
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=file_data.type,
                    comments=document_data.get('comments', '')
                )
                session.add(document)
                session.commit()
                
                # Check if all documents are collected
                self._check_documents_complete(session, employee_id)
                
                logger.info(f"Document uploaded successfully for employee {employee.employee_id}")
                
                return {
                    'success': True,
                    'message': 'Document uploaded successfully',
                    'document_id': document.id
                }
                
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return {
                'success': False,
                'message': f'Error uploading document: {str(e)}'
            }
    
    def verify_document(self, document_id: int, verified_by: str, 
                       is_verified: bool, comments: str = None) -> Dict[str, Any]:
        """Verify or reject a document"""
        try:
            with get_db_session() as session:
                document = session.query(Document).filter_by(id=document_id).first()
                
                if not document:
                    return {
                        'success': False,
                        'message': 'Document not found'
                    }
                
                document.verified = is_verified
                document.verified_by = verified_by
                document.verified_at = datetime.utcnow()
                
                if comments:
                    document.comments = comments
                
                session.commit()
                
                # Check if all documents are verified
                self._check_documents_verified(session, document.employee_id)
                
                # Send notification to employee if rejected
                if not is_verified:
                    self._send_document_rejection_email(document)
                
                return {
                    'success': True,
                    'message': f'Document {"verified" if is_verified else "rejected"} successfully'
                }
                
        except Exception as e:
            logger.error(f"Error verifying document: {str(e)}")
            return {
                'success': False,
                'message': f'Error verifying document: {str(e)}'
            }
    
    def get_employee_documents(self, employee_id: int) -> Dict[str, Any]:
        """Get all documents for an employee with status"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found',
                        'data': None
                    }
                
                # Get uploaded documents
                documents = session.query(Document).filter_by(
                    employee_id=employee_id
                ).order_by(Document.uploaded_at.desc()).all()
                
                # Get required documents
                required_docs = self.get_required_documents(employee.employee_type.value)
                
                # Create document status
                doc_status = {}
                for req_doc in required_docs:
                    doc_status[req_doc] = {
                        'uploaded': False,
                        'verified': False,
                        'document': None
                    }
                
                # Map uploaded documents
                for doc in documents:
                    if doc.document_name in doc_status:
                        doc_status[doc.document_name] = {
                            'uploaded': True,
                            'verified': doc.verified,
                            'document': doc
                        }
                
                # Calculate completion
                total_required = len(required_docs)
                uploaded_count = sum(1 for d in doc_status.values() if d['uploaded'])
                verified_count = sum(1 for d in doc_status.values() if d['verified'])
                
                return {
                    'success': True,
                    'data': {
                        'employee': employee,
                        'documents': documents,
                        'document_status': doc_status,
                        'required_documents': required_docs,
                        'total_required': total_required,
                        'uploaded_count': uploaded_count,
                        'verified_count': verified_count,
                        'completion_percentage': (verified_count / total_required * 100) if total_required > 0 else 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting employee documents: {str(e)}")
            return {
                'success': False,
                'message': f'Error getting documents: {str(e)}',
                'data': None
            }
    
    def delete_document(self, document_id: int) -> Dict[str, Any]:
        """Delete a document"""
        try:
            with get_db_session() as session:
                document = session.query(Document).filter_by(id=document_id).first()
                
                if not document:
                    return {
                        'success': False,
                        'message': 'Document not found'
                    }
                
                # Delete physical file
                if os.path.exists(document.file_path) and not config.USE_S3:
                    os.remove(document.file_path)
                elif config.USE_S3:
                    self._delete_from_s3(document.file_path)
                
                # Delete database record
                session.delete(document)
                session.commit()
                
                return {
                    'success': True,
                    'message': 'Document deleted successfully'
                }
                
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return {
                'success': False,
                'message': f'Error deleting document: {str(e)}'
            }
    
    def send_document_reminder(self, employee_id: int) -> Dict[str, Any]:
        """Send reminder email for pending documents"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Get document status
                doc_result = self.get_employee_documents(employee_id)
                if not doc_result['success']:
                    return doc_result
                
                doc_data = doc_result['data']
                pending_docs = [
                    doc_name for doc_name, status in doc_data['document_status'].items()
                    if not status['uploaded']
                ]
                
                if not pending_docs:
                    return {
                        'success': False,
                        'message': 'No pending documents'
                    }
                
                # Send reminder email
                email_data = {
                    'to_email': employee.email_personal,
                    'subject': f'Reminder: Documents Required - {employee.designation}',
                    'body_html': self._create_reminder_email_body(employee, pending_docs),
                    'body_text': f'Please upload the following pending documents: {", ".join(pending_docs)}'
                }
                
                result = self.email_sender.send_email(email_data)
                
                if result['success']:
                    # Log email
                    self.email_sender.log_email(
                        employee_id=employee_id,
                        email_data={
                            'email_type': 'document_reminder',
                            'to_email': employee.email_personal,
                            'subject': email_data['subject']
                        }
                    )
                
                return result
                
        except Exception as e:
            logger.error(f"Error sending document reminder: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending reminder: {str(e)}'
            }
    
    def _determine_document_type(self, document_name: str) -> DocumentType:
        """Determine document type from document name"""
        name_lower = document_name.lower()
        
        if any(term in name_lower for term in ['10th', '12th', 'graduation', 'degree', 'diploma', 'certificate']):
            return DocumentType.EDUCATIONAL
        elif any(term in name_lower for term in ['aadhaar', 'pan', 'passport', 'license', 'voter']):
            return DocumentType.IDENTITY
        elif any(term in name_lower for term in ['salary', 'appointment', 'relieving', 'experience']):
            return DocumentType.EMPLOYMENT
        else:
            return DocumentType.OTHER
    
    def _check_documents_complete(self, session, employee_id: int):
        """Check if all documents are collected and update checklist"""
        try:
            employee = session.query(Employee).filter_by(id=employee_id).first()
            required_docs = self.get_required_documents(employee.employee_type.value)
            
            # Get uploaded documents
            uploaded_docs = session.query(Document).filter_by(
                employee_id=employee_id
            ).all()
            
            uploaded_names = [doc.document_name for doc in uploaded_docs]
            
            # Check if all required documents are uploaded
            all_uploaded = all(req_doc in uploaded_names for req_doc in required_docs)
            
            if all_uploaded:
                # Update onboarding checklist
                checklist = session.query(OnboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                if checklist and not checklist.documents_collected:
                    checklist.documents_collected = True
                    session.commit()
                    
                    # Send notification
                    logger.info(f"All documents collected for employee {employee.employee_id}")
                    
        except Exception as e:
            logger.error(f"Error checking document completion: {str(e)}")
    
    def _check_documents_verified(self, session, employee_id: int):
        """Check if all documents are verified and update checklist"""
        try:
            # Get all documents
            documents = session.query(Document).filter_by(
                employee_id=employee_id
            ).all()
            
            # Check if all are verified
            all_verified = all(doc.verified for doc in documents) and len(documents) > 0
            
            if all_verified:
                # Update onboarding checklist
                checklist = session.query(OnboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                if checklist and not checklist.documents_verified:
                    checklist.documents_verified = True
                    session.commit()
                    
                    logger.info(f"All documents verified for employee ID {employee_id}")
                    
        except Exception as e:
            logger.error(f"Error checking document verification: {str(e)}")
    
    def _upload_to_s3(self, file_data: Any, filename: str, employee_id: str) -> Optional[str]:
        """Upload file to AWS S3"""
        try:
            import boto3
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_REGION
            )
            
            # Create S3 key
            s3_key = f"documents/{employee_id}/{filename}"
            
            # Upload file
            s3_client.put_object(
                Bucket=config.AWS_S3_BUCKET,
                Key=s3_key,
                Body=file_data.getvalue(),
                ContentType=file_data.type
            )
            
            # Return S3 URL
            return f"https://{config.AWS_S3_BUCKET}.s3.{config.AWS_REGION}.amazonaws.com/{s3_key}"
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            return None
    
    def _delete_from_s3(self, s3_url: str):
        """Delete file from AWS S3"""
        try:
            import boto3
            
            # Extract key from URL
            s3_key = s3_url.split('.com/')[-1]
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_REGION
            )
            
            s3_client.delete_object(
                Bucket=config.AWS_S3_BUCKET,
                Key=s3_key
            )
            
        except Exception as e:
            logger.error(f"Error deleting from S3: {str(e)}")
    
    def _create_reminder_email_body(self, employee: Employee, pending_docs: List[str]) -> str:
        """Create reminder email body"""
        return f"""
        <p>Dear {employee.full_name},</p>
        
        <p>This is a reminder to upload the following pending documents for your joining process:</p>
        
        <ul>
            {''.join(f'<li>{doc}</li>' for doc in pending_docs)}
        </ul>
        
        <p>Please upload these documents at your earliest convenience to complete your onboarding process.</p>
        
        <p>If you have any questions or face any issues, please feel free to reach out to us.</p>
        
        <p>Best regards,<br>
        Team HR<br>
        Rapid Innovation</p>
        """
    
    def _send_document_rejection_email(self, document: Document):
        """Send email notification for document rejection"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=document.employee_id).first()
                
                if employee:
                    email_data = {
                        'to_email': employee.email_personal,
                        'subject': f'Document Rejected - {document.document_name}',
                        'body_html': f"""
                        <p>Dear {employee.full_name},</p>

                        <p>Your document "{document.document_name}" has been rejected.</p>

                        <p><strong>Reason:</strong> {document.comments or 'Document does not meet requirements'}</p>

                        <p>Please upload a new copy of this document.</p>

                        <p>Best regards,<br>
                        Team HR<br>
                        Rapid Innovation</p>
                        """,
                        'body_text': f'Your document {document.document_name} has been rejected. Please upload a new copy.'
                    }

                    # Send the email
                    result = self.email_sender.send_email(email_data)

                    if result['success']:
                        # Log email
                        self.email_sender.log_email(
                            employee_id=document.employee_id,
                            email_data={
                                'email_type': 'document_rejection',
                                'to_email': employee.email_personal,
                                'subject': email_data['subject']
                            }
                        )
                        logger.info(f"Document rejection email sent to {employee.email_personal}")
                    else:
                        logger.error(f"Failed to send document rejection email: {result['message']}")

        except Exception as e:
            logger.error(f"Error sending document rejection email: {str(e)}")