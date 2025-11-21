"""
Templates API endpoints
"""
from flask import Blueprint, jsonify, request
from app.models import Storage

bp = Blueprint('templates', __name__, url_prefix='/api/templates')

@bp.route('', methods=['GET'])
def get_templates():
    """Get all templates"""
    templates = Storage.load('templates')
    return jsonify(templates)

@bp.route('/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get a specific template"""
    template = Storage.get('templates', template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    return jsonify(template)

@bp.route('', methods=['POST'])
def create_template():
    """Create a new template"""
    data = request.json
    
    body = data.get('body', '').strip()
    html_body = data.get('html_body', '').strip()
    
    # Validate that at least one body exists
    if not body and not html_body:
        return jsonify({'error': 'Either plain text body or HTML body (or both) must be provided'}), 400
    
    template = {
        'name': data.get('name', 'Untitled Template'),
        'subject': data.get('subject', ''),
        'body': body,
        'html_body': html_body,
        'description': data.get('description', '')
    }
    
    template = Storage.add('templates', template)
    return jsonify(template), 201

@bp.route('/<template_id>', methods=['PUT'])
def update_template(template_id):
    """Update a template"""
    data = request.json
    
    # Get existing template to merge with updates
    existing = Storage.get('templates', template_id)
    if not existing:
        return jsonify({'error': 'Template not found'}), 404
    
    # Merge updates
    body = data.get('body', existing.get('body', '')).strip() if 'body' in data else existing.get('body', '').strip()
    html_body = data.get('html_body', existing.get('html_body', '')).strip() if 'html_body' in data else existing.get('html_body', '').strip()
    
    # Validate that at least one body exists
    if not body and not html_body:
        return jsonify({'error': 'Either plain text body or HTML body (or both) must be provided'}), 400
    
    # Update data with validated body fields
    update_data = data.copy()
    update_data['body'] = body
    update_data['html_body'] = html_body
    
    template = Storage.update('templates', template_id, update_data)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    return jsonify(template)

@bp.route('/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a template"""
    if Storage.delete('templates', template_id):
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'Template not found'}), 404

@bp.route('/<template_id>/preview', methods=['POST'])
def preview_template(template_id):
    """Preview a template with sample data"""
    template = Storage.get('templates', template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    sample_data = request.json.get('sample_data', {
        'FirstName': 'John',
        'LastName': 'Doe',
        'Brokerage': 'ABC Realty',
        'City': 'New York',
        'State': 'NY',
        'Custom1': 'Commercial',
        'Custom2': '5 years'
    })
    
    try:
        from src import TemplateProcessor
        processor = TemplateProcessor()
        
        rendered_subject = processor.get_rendered_subject(template.get('subject', ''), sample_data)
        rendered_body = processor.get_rendered_body(template.get('body', ''), sample_data)
        rendered_html = None
        if template.get('html_body'):
            rendered_html = processor.get_rendered_html(template.get('html_body', ''), sample_data)
        
        return jsonify({
            'subject': rendered_subject,
            'body': rendered_body,
            'html_body': rendered_html
        })
    except Exception as e:
        return jsonify({'error': f'Error rendering template: {str(e)}'}), 400

