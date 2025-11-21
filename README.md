# Email Outreach Platform

A full-featured web-based email outreach platform built with Python and Flask. Manage SMTP accounts, contacts, templates, and campaigns through an intuitive web interface.

## Features

- **Web-Based Dashboard**: Real-time statistics and campaign monitoring
- **SMTP Account Management**: Add, edit, and test multiple SMTP accounts with rotation
- **Contact Management**: Upload CSV files or add contacts manually
- **Template System**: Create email templates with dynamic variables (GMass-style)
- **Campaign Management**: Create and run email campaigns with real-time progress tracking
- **Automated Follow-ups**: Rule-based follow-up system (coming soon)
- **Rate Limiting**: Built-in throttling and batching for deliverability

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure SMTP Accounts

Add your SMTP accounts through the web interface at `/accounts` or configure them in `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=Your Name
```

### 3. Run the Platform

```bash
python run.py
```

The platform will be available at `http://localhost:5000`

## Usage

### Dashboard

Visit the homepage to see:
- Total campaigns and emails sent
- Contact statistics
- SMTP account status
- Recent campaign activity

### Managing SMTP Accounts

1. Go to **SMTP Accounts** page
2. Click **+ Add SMTP Account**
3. Fill in your SMTP credentials
4. Click **Test Connection** to verify
5. Save the account

You can add multiple accounts for automatic rotation.

### Managing Contacts

1. Go to **Contacts** page
2. Upload a CSV file or add contacts manually
3. CSV should include: `email`, `first_name`, `last_name`, `company`, `brokerage`, `city`, `state`, `custom1-5`

### Creating Templates

1. Go to **Templates** page
2. Click **+ Create Template**
3. Use variables like `{FirstName}`, `{Brokerage}`, `{City}`, `{Custom1}`, etc.
4. Preview your template before saving

### Running Campaigns

1. Go to **Campaigns** page
2. Click **+ Create Campaign**
3. Select a template
4. Choose contacts (or leave empty for all pending)
5. Set max emails if needed
6. Click **Create Campaign**
7. Click **Start** to begin sending

Monitor progress in real-time on the campaigns page.

## API Endpoints

The platform provides a REST API:

- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/campaigns` - List campaigns
- `POST /api/campaigns` - Create campaign
- `POST /api/campaigns/<id>/start` - Start campaign
- `GET /api/contacts` - List contacts
- `POST /api/contacts/upload` - Upload CSV
- `GET /api/templates` - List templates
- `GET /api/smtp-accounts` - List SMTP accounts

## Template Variables

Available variables in templates:
- `{FirstName}`, `{LastName}`, `{FullName}`
- `{Email}`, `{Company}`, `{Brokerage}`
- `{City}`, `{State}`
- `{Custom1}` through `{Custom5}`

## Architecture

- **Backend**: Flask web framework
- **Storage**: JSON-based file storage (simple, no database required)
- **Email Engine**: Built on the `src/` modules for SMTP management
- **Frontend**: Modern HTML/CSS/JavaScript with responsive design

## File Structure

```
email-sender/
├── app/
│   ├── api/          # API endpoints
│   ├── models/       # Data models and storage
│   ├── static/       # CSS and JavaScript
│   └── templates/    # HTML templates
├── src/              # Core email sending modules
├── data/             # JSON storage (auto-created)
├── uploads/          # Uploaded files (auto-created)
└── run.py           # Application entry point
```

## Configuration

Set environment variables:
- `PORT` - Server port (default: 5000)
- `FLASK_ENV` - Set to `development` for debug mode
- `SECRET_KEY` - Flask secret key (change in production)

## Production Deployment

1. Set `SECRET_KEY` environment variable
2. Use a production WSGI server (gunicorn, uwsgi)
3. Configure reverse proxy (nginx)
4. Enable HTTPS
5. Set up proper file permissions for `data/` and `uploads/` directories

Example with gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Security Notes

- Never commit `.env` files or credentials
- Use app-specific passwords for Gmail
- Change `SECRET_KEY` in production
- Consider using environment variables or secret management
- The platform stores SMTP passwords in JSON files - secure the `data/` directory

## License

This project is provided as-is for educational and commercial use.
