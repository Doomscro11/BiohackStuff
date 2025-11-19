# Peptimancer

AI-powered platform for peptide design and patent opportunity mining.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB
- Docker (optional)

### Local Development

1. **Start all services:**
   ```bash
   sudo supervisorctl restart all
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8001
   - API Docs: http://localhost:8001/docs

3. **View logs:**
   ```bash
   # Backend
   tail -f /var/log/supervisor/backend.err.log
   
   # Frontend
   tail -f /var/log/supervisor/frontend.out.log
   ```

### Project Structure

```
/app/
├── backend/          # FastAPI backend
│   ├── api/          # API routes (thin controllers)
│   ├── services/     # Business logic
│   ├── models/       # Database models
│   ├── schemas/      # API DTOs
│   ├── jobs/         # Background tasks
│   └── middleware/   # Auth, logging, etc.
├── frontend/         # React frontend
│   └── src/
│       ├── apps/     # Domain pages
│       ├── components/ # Shared UI
│       └── lib/      # Utilities
└── docs/             # Documentation
```

## Features

### Core Capabilities

- **Peptide Design:** AI-powered peptide analogue generation
- **PatentPulse:** Patent mining and opportunity analysis
- **Partner Portal:** Secure share links with watermarking
- **Admin Dashboard:** User management and analytics
- **Billing:** Stripe integration for subscriptions

### Technology Stack

- **Backend:** FastAPI, MongoDB, JWT auth
- **Frontend:** React 18, Shadcn UI
- **Infrastructure:** Docker, Kubernetes, Supervisor

## Documentation

- [Architecture Guide](./ARCHITECTURE.md) - System design and patterns
- [API Reference](./API_REFERENCE.md) - Endpoint documentation
- [Partner Portal](./docs/PARTNER_PORTAL.md) - Partner sharing guide
- [PatentPulse](./docs/README_PATENTPULSE.md) - Patent mining docs

## Development

### Adding a New Feature

1. Create service in `backend/services/`
2. Define schemas in `backend/schemas/`
3. Create route in `backend/api/`
4. Build frontend in `frontend/src/apps/`
5. Add route to `MainApp.js`

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed patterns.

### Running Tests

**Backend:**
```bash
pytest backend/tests/
python backend/scripts/verify_partner_portal.py
```

**Frontend:**
```bash
cd frontend && yarn test
```

## Configuration

### Environment Variables

**Backend (.env):**
```bash
MONGO_URL=mongodb://localhost:27017
ADMIN_EMAILS=admin@peptimancer.com
STRIPE_SECRET_KEY=sk_...
PARTNER_SIGNING_SECRET=...
```

**Frontend (.env):**
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for complete variable list.

## Deployment

### Docker

```bash
docker-compose up -d
```

### Kubernetes

Deploy to cluster with provided manifests:
```bash
kubectl apply -f k8s/
```

## Monitoring

- Health: `GET /api/admin/health`
- Metrics: Admin dashboard at `/admin/analytics`
- Logs: Supervisor and application logs

## Security

- JWT authentication with magic links
- Role-based access control
- HMAC-signed share tokens
- Watermarked PDF exports
- Rate limiting on auth endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For issues or questions, file an issue or contact the development team
