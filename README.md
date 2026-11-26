
# Shivrai Group — Website & Admin Dashboard

Full-stack real estate website and administration platform for **Shivrai Group**.

The project includes a public website, project management dashboard, media library, enquiry management, authentication, and project analytics.

## 1. Technology Stack

| Component | Technology |
|---|---|
| Frontend | Angular 22, TypeScript, SCSS |
| Backend | Python, FastAPI |
| Database | MongoDB |
| Database Driver | PyMongo |
| Image Storage | Cloudinary |
| Authentication | JWT |
| API Documentation | FastAPI Swagger UI |
| Version Control | Git & GitHub |

## 2. Features

### Public Website

- Responsive homepage
- Projects listing with search and pagination
- Project details pages
- Project cover images and galleries
- Horizontal image gallery slider
- Residential and commercial project categories
- Project status filtering
- Contact enquiry form
- Success message followed by redirect to homepage
- Click-based navigation dropdowns
- About, Offices, Retail and Careers navigation

### Admin Dashboard

- Secure admin login
- JWT-based authentication
- Dashboard statistics
- Project creation, editing and deletion
- Project status and category management
- Project image upload and selection
- Media library using Cloudinary
- Cover image and gallery management
- Image cropping
- Gallery image reordering
- Contact enquiry management
- Project view analytics
- Dark and light theme toggle

## 3. Project Structure

The repository contains the Angular frontend and FastAPI backend.

### Frontend

```text
Frontend/
└── angular/
    └── src/
        └── app/
            ├── pages/
            │   ├── home/
            │   ├── projects/
            │   ├── project-details/
            │   └── contact/
            ├── services/
            ├── app.html
            ├── app.scss
            └── app.ts
```

The frontend also contains the admin components for the dashboard, projects, enquiries, and media library.

### Backend

The backend uses FastAPI with MongoDB.

Major functionality includes:

- Authentication
- Projects API
- Contact enquiries API
- Media uploads and management
- Project analytics

Check the backend source for the exact router and module structure.

## 4. Setting Up the Project

### Prerequisites

Install:

- Python
- Node.js and npm
- Angular CLI
- MongoDB or a MongoDB Atlas connection
- Git

Cloudinary credentials are required for image-management functionality.

### Clone Repository

```bash
git clone <repository-url>
cd shivrai-group
```

Replace `<repository-url>` with the actual GitHub repository URL.

### Backend Setup

From the backend directory, create a Python virtual environment:

```powershell
python -m venv venv
```

Activate it in Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies using the repository's requirements file:

```powershell
pip install -r requirements.txt
```

Configure the backend environment variables before starting the server.

### Backend Environment Variables

The backend uses configuration for:

- MongoDB connection
- JWT secret key
- Admin username
- Admin password hash
- Cloudinary credentials

Known authentication variables include:

```env
ADMIN_USERNAME=
ADMIN_PASSWORD_HASH=
JWT_SECRET_KEY=
```

Use the actual environment variable names defined in the backend source for MongoDB and Cloudinary.

Do not commit `.env` files, passwords, API secrets, or private keys.

### Run the Backend

From the directory containing the FastAPI application:

```powershell
uvicorn main:app --reload
```

If the entry point is located inside a Python package, adjust the module path.

Common development endpoints:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

The `/docs` page provides interactive API documentation.

### Frontend Setup

Navigate to:

```powershell
cd Frontend/angular
```

Install dependencies:

```powershell
npm install
```

Start the Angular development server:

```powershell
ng serve
```

Alternatively, use the development script configured in `package.json`.

The frontend is typically available at:

```text
http://localhost:4200
```

Make sure the frontend API configuration points to the correct backend URL.

## 5. Backend API Overview

### Authentication

```http
POST /auth/login
```

Used for admin authentication.

Protected endpoints require a valid JWT bearer token.

### Projects

```http
GET    /projects
GET    /projects/{id}
POST   /projects
PUT    /projects/{id}
DELETE /projects/{id}
```

Project endpoints support management of real estate developments.

The listing functionality supports filtering, searching, sorting, and pagination.

### Project Analytics

```http
POST /projects/{id}/view
```

Records project views.

The frontend only triggers view tracking in the browser to avoid counting server-side rendering requests.

### Contact Enquiries

```http
POST /contact
```

Allows visitors to submit enquiries.

Additional protected endpoints allow administrators to view and manage submitted enquiries.

### Media Management

The backend includes Cloudinary-backed media functionality.

Check Swagger UI for the exact upload, image management, deletion, and image-selection endpoints.

## 6. Project Data Model

Project records include fields such as:

| Field | Purpose |
|---|---|
| `id` | Unique project identifier |
| `name` | Project name |
| `status` | Ongoing, Completed, Upcoming |
| `category` | Residential, Commercial, Retail, Offices |
| `location` | Project location |
| `description` | Project overview |
| `image` | Main cover image URL |
| `image_public_id` | Cloudinary cover image identifier |
| `gallery` | Array of gallery image URLs |
| `gallery_assets` | Gallery media metadata |
| `total_views` | Total view count |
| `daily_views` | Daily view analytics |

Maintain compatibility between the backend response model and Angular interfaces when adding fields.

## 7. Frontend Development Notes

### Public Homepage

Location:

```text
Frontend/angular/src/app/pages/home/
```

Contains the main landing page.

The current design uses:

- Architectural hero section
- Company introduction
- Development showcase
- Residential and commercial sections
- Company statement
- Contact CTA

The initial design uses placeholder architectural photographs. These should be replaced with approved Shivrai Group imagery.

### Projects Page

Location:

```text
Frontend/angular/src/app/pages/projects/
```

Features include:

- Project listing
- Cover image display
- Search
- Pagination
- Project details navigation

The intended pagination limit is **6 projects per page**.

### Project Details Page

Location:

```text
Frontend/angular/src/app/pages/project-details/
```

Includes:

- Project title and location
- Cover image
- Project information
- Description
- Horizontal image gallery
- Previous and next gallery controls
- Enquiry CTA

The gallery uses `viewChild` and `ElementRef` to scroll through images.

### Contact Page

Location:

```text
Frontend/angular/src/app/pages/contact/
```

The contact form collects:

- Name
- Email
- Phone
- Optional subject
- Message

After successful submission, the user sees a confirmation message for **3 seconds**, then returns to the homepage.

### Main Navigation

Files:

```text
Frontend/angular/src/app/app.html
Frontend/angular/src/app/app.scss
Frontend/angular/src/app/app.ts
```

The public header uses warm ivory, taupe, and bronze colours.

Dropdowns open on click rather than hover.

Main navigation:

- Home
- Projects
- Commercial
  - Offices
  - Retail
- About
- Careers
- Contact

Admin navigation is separate from public navigation.

## 8. Admin Development Notes

The admin panel manages the website's content.

### Authentication

Admin routes must remain protected.

Do not expose admin credentials or secrets in frontend code.

### Project Management

Administrators can:

- Create projects
- Edit project information
- Change project status and category
- Select cover images
- Assign gallery images
- Delete projects

### Media Library

Media functionality includes:

- Uploading images
- Selecting existing images
- Managing cover images
- Managing galleries
- Cropping images
- Reordering gallery images
- Removing unused media

Image assets are stored using Cloudinary.

### Analytics

Project views are tracked through the backend.

Maintain the distinction between browser-side user views and server-side rendering.

## 9. Important Development Rules

### Preserve Existing Functionality

Before making changes:

1. Inspect the existing component and service.
2. Check the corresponding backend API.
3. Preserve existing data-loading and authentication logic.
4. Avoid unnecessary changes to working modules.
5. Verify that new features do not break existing pages.

### Angular

- Follow the project's standalone-component structure.
- Use the existing Angular services for API communication.
- Keep templates, TypeScript, and SCSS organized.
- Preserve server-side rendering compatibility.
- Avoid direct browser API usage during SSR.
- Use responsive layouts.

### Backend

- Validate incoming data using Pydantic.
- Keep authentication on protected endpoints.
- Preserve API response compatibility.
- Handle database and Cloudinary errors safely.
- Never expose secrets in API responses.

### Database

- Use MongoDB for persistent project and enquiry records.
- Avoid destructive data migrations without a backup.
- Preserve compatibility with existing records.

## 10. Known Areas for Improvement

The next developer should review these areas:

### High Priority

- Replace temporary homepage images with actual project imagery.
- Verify that navigation query parameters correctly filter projects.
- Validate all public routes.
- Test mobile navigation and dropdown behaviour.
- Review responsiveness across screen sizes.

### Medium Priority

- Improve project gallery with a full-screen lightbox.
- Add loading placeholders for project images.
- Improve SEO metadata.
- Add image-loading error fallbacks.
- Improve accessibility and keyboard navigation.

### Before Production

- Verify CORS configuration.
- Configure production environment variables.
- Review JWT and admin security.
- Validate form submissions.
- Test image uploads and deletion.
- Configure deployment and HTTPS.
- Test all critical frontend and backend flows.

## 11. Git Workflow

The project has been developed directly on the `main` branch.

Latest known synchronized commit:

```text
b1ebc45
Update homepage, navigation, project gallery and contact flow
```

### Pull Latest Changes

```powershell
git switch main
git pull origin main
```

### Check Changes

```powershell
git status
git diff
```

### Commit and Push

```powershell
git add .
git commit -m "Describe changes made"
git push origin main
```

Review staged changes before committing.

Do not commit:

- `.env` files
- Virtual environments
- `node_modules`
- Secret keys
- Database credentials
- Build artifacts

Coordinate changes when multiple developers are working on `main` to avoid overwriting one another.

## 12. Developer Handover Checklist

Before continuing development:

- [ ] Clone the latest repository
- [ ] Install frontend dependencies
- [ ] Create the Python virtual environment
- [ ] Install backend dependencies
- [ ] Configure MongoDB credentials
- [ ] Configure Cloudinary credentials
- [ ] Configure admin authentication secrets
- [ ] Start the backend
- [ ] Start the Angular frontend
- [ ] Verify API connectivity
- [ ] Test admin login
- [ ] Test project listing and details
- [ ] Test gallery image loading
- [ ] Test contact enquiry submission
- [ ] Test admin media management
- [ ] Review outstanding development tasks

---

## Project Status

**Status:** Active Development

**Primary branch:** `main`

**Latest known commit:** `b1ebc45`

The public website and admin platform have their core functionality implemented. Further development should focus on design refinement, integration testing, security review, real content, and production readiness.

**Shivrai Group — Website Development**
