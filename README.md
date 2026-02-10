# ICT Help Desk System
## Requirements Analysis Report & Software Design Document

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Requirements Analysis](#requirements-analysis)
3. [System Architecture](#system-architecture)
4. [Software Design](#software-design)
5. [Database Design](#database-design)
6. [Technical Specifications](#technical-specifications)

---

## Executive Summary

The ICT Help Desk System is a web-based ticketing platform designed to streamline IT support operations. It enables users to submit technical issues, track their progress, and allows administrators to manage, assign, and resolve tickets efficiently. The system provides real-time notifications and comprehensive analytics for management oversight.

**Key Objectives:**
- Simplify issue submission and tracking for end-users
- Improve issue resolution workflow for IT staff
- Provide management with actionable insights through dashboards
- Ensure efficient communication through automated notifications

---

## Requirements Analysis

### 1. User Registration & Authentication

#### Functional Requirements
| Requirement | Description |
|---|---|
| **FR1.1** | Users shall register using Email and Mobile Number |
| **FR1.2** | Email addresses from CU domain (@cu.*) shall be automatically marked as verified users |
| **FR1.3** | Registration shall collect: Name, Email, Mobile, Address, Office/Department |
| **FR1.4** | Non-CU domain emails require manual verification before system access |

#### Non-Functional Requirements
| Requirement | Description |
|---|---|
| **NFR1.1** | Email validation must be RFC 5322 compliant |
| **NFR1.2** | Mobile number validation must support local and international formats |
| **NFR1.3** | Password security must comply with industry standards (minimum 8 characters, mixed case, numbers, special characters) |

---

### 2. Issue Submission

#### Functional Requirements
| Requirement | Description |
|---|---|
| **FR2.1** | System shall generate a unique Ticket ID using shortest possible random string algorithm |
| **FR2.2** | Each submission shall have a default Status of "Submitted" |
| **FR2.3** | Users shall be able to select an Issue Category and Subcategory |
| **FR2.4** | Users shall specify the Location of the issue |
| **FR2.5** | Users shall provide detailed description of the issue |
| **FR2.6** | File attachments shall be optional (document/image files) |
| **FR2.7** | System shall validate all required fields before ticket creation |

#### Issue Status Workflow
```
Submitted → In Progress → Solved
```

#### Non-Functional Requirements
| Requirement | Description |
|---|---|
| **NFR2.1** | Ticket ID generation must be collision-free |
| **NFR2.2** | Ticket ID should be 6-8 characters maximum for user convenience |
| **NFR2.3** | File attachment size limit: 25 MB per file, maximum 5 files |
| **NFR2.4** | Supported file types: PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, JPEG, GIF |

---

### 3. Issue Tracking

#### Functional Requirements
| Requirement | Description |
|---|---|
| **FR3.1** | Users shall be able to search issues using Ticket ID |
| **FR3.2** | System shall display current status of the ticket |
| **FR3.3** | Issue tracking shall be accessible without user login |
| **FR3.4** | Users shall view issue history and all status updates |

#### Non-Functional Requirements
| Requirement | Description |
|---|---|
| **NFR3.1** | Search results must load within 2 seconds |
| **NFR3.2** | Public tracking must be rate-limited to prevent abuse |

---

### 4. Notification System

#### 4.1 Issue Submitter Notifications
| Event | Delivery Method | Content |
|---|---|---|
| User Registration | Email | Welcome message + account verification |
| Issue Submission | Email + SMS | Ticket ID + status confirmation |
| Staff Assignment | Email | Staff name + contact information |
| Issue Resolution | Email | Solution details + feedback request |

#### 4.2 Super Admin Notifications
| Event | Delivery Method | Trigger |
|---|---|---|
| New Issue Submitted | Email/Dashboard Alert | Immediately upon submission |
| Issue Marked Solved | Email/Dashboard Alert | When staff updates status to "Solved" |

#### 4.3 Staff Notifications
| Event | Delivery Method | Trigger |
|---|---|---|
| Assignment | Email | When super admin assigns ticket to staff |

#### Non-Functional Requirements
| Requirement | Description |
|---|---|
| **NFR4.1** | Email delivery within 5 minutes of event |
| **NFR4.2** | SMS delivery within 2 minutes of submission |
| **NFR4.3** | Notification retry mechanism for failed deliveries |

---

### 5. Super Admin Dashboard & Controls

#### Functional Requirements
| Requirement | Description |
|---|---|
| **FR5.1** | Dashboard shall display graphical view of submissions by date range |
| **FR5.2** | Dashboard shall display graphical view of submissions by office/department |
| **FR5.3** | Dashboard shall display task completion metrics by assigned staff |
| **FR5.4** | Super admin shall have authority to assign tickets to staff members |
| **FR5.5** | Super admin shall be able to view all issues in the system |
| **FR5.6** | Super admin shall be able to change issue status |
| **FR5.7** | Super admin shall be able to create and manage issue categories and subcategories |
| **FR5.8** | Super admin shall be able to add and modify issue priority levels |

#### Dashboard Metrics
```
- Total submissions (daily, weekly, monthly views)
- Submissions by department/office
- Staff performance metrics (issues assigned, resolved, pending)
- Average resolution time
- Priority distribution
```

#### Non-Functional Requirements
| Requirement | Description |
|---|---|
| **NFR5.1** | Dashboard load time must be under 3 seconds |
| **NFR5.2** | Charts must be responsive and mobile-friendly |
| **NFR5.3** | Data refresh interval: real-time for critical updates, 5-minute cache for analytics |

---

## System Architecture

### 3-Tier Architecture

```
┌─────────────────────────────────────────┐
│       Presentation Layer (UI)           │
│  (Web Interface, Mobile Responsive)     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   Application Layer (Business Logic)    │
│  (APIs, Controllers, Services)          │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│     Data Layer (Database & Storage)     │
│  (User, Ticket, Category, Notification) │
└─────────────────────────────────────────┘
```

### External Services
- **Email Service**: Google SMTP for email notifications
- **SMS Service**: Custom Robi API for SMS notifications
- **File Storage**: Cloud storage (AWS S3, Azure Blob, or local)

---

## Software Design

### Design Patterns & Principles

1. **Model-View-Controller (MVC)** - Separation of concerns
2. **Service Layer Pattern** - Business logic abstraction
3. **Repository Pattern** - Data access abstraction
4. **Factory Pattern** - Ticket ID generation
5. **Observer Pattern** - Notification system
6. **SOLID Principles** - Maintainability and scalability

---

### Core Modules

#### 1. Authentication Module
```
├── User Registration Service
├── Email Verification Service
├── CU Domain Detection
└── Password Management
```

#### 2. Ticket Management Module
```
├── Ticket Submission Service
├── Ticket ID Generator
├── Status Management Service
├── Attachment Handler
├── Category/Subcategory Manager
└── Priority Manager
```

#### 3. Tracking Module
```
├── Ticket Search Service
├── Status Query Service
├── Public Access Controller
└── History Viewer
```

#### 4. Notification Module
```
├── Email Notification Service
├── SMS Notification Service
├── Notification Queue Manager
├── Event Listener
└── Notification Template Engine
```

#### 5. Admin Dashboard Module
```
├── Analytics Service
├── Report Generator
├── User Assignment Service
├── Category Management Service
├── Dashboard Controller
└── Chart/Graph Generator
```

---

### Use Case Diagram

```
                                ┌─────────────────┐
                                │  ICT Help Desk  │
                                │     System      │
                                └─────────────────┘
                                        │
                    ┌───────────────────┼──────────────┐
                    │                   │              │
              ┌─────▼───────┐    ┌──────▼────┐  ┌──────▼─────┐
              │  User       │    │ Staff     │  │ SuperAdmin │
              │(Registrant) │    │(Member)   │  │            │
              └────┬────────┘    └──────┬────┘  └───┬────────┘
                   │               │           │
         ┌─────────┼───────────────┼───────────┼──────────┐
         │         │               │           │          │
    ┌────▼───┐  ┌──▼────┐  ┌───────▼──┐  ┌────▼──┐  ┌────▼────┐
    │Register│  │Submit │  │  Track   │  │Receive│  │Dashboard│
    │        │  │ Issue │  │  Issue   │  │Notify │  │Analytics│
    └────────┘  └───────┘  └──────────┘  └───────┘  └─────────┘
         │         │            │            │          │
         │         │            └────────────┼──────────┘
         │         │                         │
         └─────────┼─────────────────────────┘
                   │
            ┌──────▼───────┐
            │ Notification │
            │   System     │
            └──────────────┘
```

---

## Database Design

### Entity-Relationship Diagram

```
┌──────────────────┐         ┌──────────────────┐
│      Users       │         │  IssueCategory   │
├──────────────────┤         ├──────────────────┤
│ UserID (PK)      │         │ CategoryID (PK)  │
│ Email            │         │ CategoryName     │
│ MobileNumber     │         │ Description      │
│ FullName         │         └──────────────────┘
│ Address          │                  △
│ Department       │                  │
│ IsVerified       │                  │
│ DateRegistered   │                  │
│ Role             │                  │
└──────────────────┘                  │
         △                            │
         │ (Creates)          (Belongs To)
         │                            │
         │         ┌──────────────────┴─────────┐
         │         │                            │
    ┌────┴────────────────┐          ┌──────────▼─────────┐
    │      Tickets        │          │ IssueSubcategory   │
    ├─────────────────────┤          ├────────────────────┤
    │ TicketID (PK)       │          │ SubcategoryID (PK) │
    │ SubmitterID (FK)    │◄─┐       │ CategoryID (FK)    │
    │ AssignedToID (FK)   │  │       │ SubcategoryName    │
    │ CategoryID (FK)     │  │       │ Description        │
    │ SubcategoryID (FK)  │  │       └────────────────────┘
    │ Priority            │  │
    │ Status              │  │
    │ Location            │  │
    │ Description         │  │
    │ DateCreated         │  │
    │ DateResolved        │  │
    │ LastUpdated         │  │
    └─────────────────────┘  │
                             │
                        ┌────┴──────────┐
                        │ Staff Members │
                        ├───────────────┤
                        │ StaffID (PK)  │
                        │ UserID (FK)   │
                        │ Department    │
                        │ IsActive      │
                        └───────────────┘

┌────────────────────┐         ┌──────────────────┐
│   Attachments      │         │  Notifications   │
├────────────────────┤         ├──────────────────┤
│ AttachmentID (PK)  │         │ NotificationID(PK)│
│ TicketID (FK)      │         │ RecipientID (FK) │
│ FileName           │         │ TicketID (FK)    │
│ FileType           │         │ EventType        │
│ FilePath           │         │ MessageType      │
│ FileSize           │         │ Status           │
│ DateUploaded       │         │ DateSent         │
└────────────────────┘         └──────────────────┘
```

### Key Tables

#### Users Table
```sql
CREATE TABLE Users (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Email VARCHAR(255) UNIQUE NOT NULL,
    MobileNumber VARCHAR(20) NOT NULL,
    FullName VARCHAR(255) NOT NULL,
    Address TEXT,
    Department VARCHAR(100),
    IsVerified BOOLEAN DEFAULT FALSE,
    DateRegistered DATETIME DEFAULT CURRENT_TIMESTAMP,
    Role ENUM('User', 'Staff', 'SuperAdmin') DEFAULT 'User',
    PasswordHash VARCHAR(255) NOT NULL,
    LastLogin DATETIME
);
```

#### Tickets Table
```sql
CREATE TABLE Tickets (
    TicketID VARCHAR(10) PRIMARY KEY,
    SubmitterID INT NOT NULL,
    AssignedToID INT,
    CategoryID INT NOT NULL,
    SubcategoryID INT NOT NULL,
    Priority ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
    Status ENUM('Submitted', 'In Progress', 'Solved') DEFAULT 'Submitted',
    Location VARCHAR(255),
    Description LONGTEXT NOT NULL,
    DateCreated DATETIME DEFAULT CURRENT_TIMESTAMP,
    DateResolved DATETIME,
    LastUpdated DATETIME,
    FOREIGN KEY (SubmitterID) REFERENCES Users(UserID),
    FOREIGN KEY (AssignedToID) REFERENCES Users(UserID),
    FOREIGN KEY (CategoryID) REFERENCES IssueCategory(CategoryID),
    FOREIGN KEY (SubcategoryID) REFERENCES IssueSubcategory(SubcategoryID),
    INDEX idx_status (Status),
    INDEX idx_submitter (SubmitterID),
    INDEX idx_assigned (AssignedToID)
);
```

---

## Technical Specifications

### Technology Stack Recommendations

| Layer | Technologies |
|---|---|
| **Frontend** | React.js with TailwindCSS, HTML5, JavaScript/TypeScript (ES6+) |
| **Build Tool** | Vite.js for fast development and optimized builds |
| **Backend** | Node.js with Express.js, JavaScript/TypeScript |
| **ORM** | Sequelize or TypeORM |
| **Database** | MySQL 8.0+ |
| **Authentication** | JWT tokens |
| **File Storage** | DigitalOcean Spaces |
| **Email Service** | Google SMTP |
| **SMS Service** | Custom Robi API |
| **Type Safety** | TypeScript (Optional for both Frontend & Backend) |

### TypeScript Implementation (Optional)

**Benefits of TypeScript:**
- Static type checking catches errors at compile-time
- Enhanced IDE support with intelligent code completion
- Self-documenting code through type annotations
- Easier refactoring across large codebases
- Better collaboration in team environments
- Seamless integration with JavaScript libraries

**Frontend TypeScript Setup:**
- Define types for React component props using interfaces/types
- Type API responses from backend endpoints
- Create shared type definitions for models (User, Ticket, Category, etc.)
- Use TypeScript strict mode for maximum type safety
- Build configuration: Vite automatically handles TypeScript compilation
- Example: `tsconfig.json` with `strict: true`, `jsx: "react-jsx"`

**Backend TypeScript Setup:**
- Type Express request/response objects using middleware typing
- Define database model types matching Sequelize/TypeORM entities
- Create service layer type definitions for business logic
- Use TypeScript decorators (if using TypeORM)
- Build step: Compile TypeScript to JavaScript before running on Node.js
- Example: `ts-node` for development, `tsc` for production builds

**Recommended TypeScript Packages:**
- `@types/express` - Type definitions for Express
- `@types/node` - Type definitions for Node.js
- `@types/react` - Type definitions for React
- `@types/react-dom` - Type definitions for React DOM
- `typescript` - TypeScript compiler

### ORM Implementation Details

**Sequelize.js** (Recommended for Node.js/Express)
- Promise-based ORM for relational databases
- Built-in migrations and seeders for database versioning
- Automatic type casting and validation
- Support for associations (HasMany, BelongsTo, etc.)
- Connection pooling for better performance
- Transaction support for data integrity

**Key ORM Features to Utilize:**
- **Model Definitions**: Define User, Ticket, Category, Subcategory, Attachment, Notification models
- **Associations**: Define relationships between entities (User → Tickets, Tickets → Attachments, etc.)
- **Validations**: Built-in validators for email, length, uniqueness constraints
- **Hooks**: Use before/after hooks for automatic timestamps, hashing passwords, etc.
- **Migrations**: Version control for database schema changes
- **Query Optimization**: Eager loading to reduce database queries

### Security Requirements

| Requirement | Implementation |
|---|---|
| **Authentication** | JWT tokens for user sessions |
| **Authorization** | Basic role-based access (User, Staff, SuperAdmin) |
| **Data Encryption** | SSL/TLS for data in transit |
| **Input Validation** | Server-side validation for all inputs |
| **SQL Injection Prevention** | Prepared statements and parameterized queries |
| **CSRF Protection** | Token-based CSRF protection |


### Deployment Architecture

```
┌───────────────────────────────────────────────────────┐
│      React.js Frontend (Static)                       │
│  (DigitalOcean Spaces or CDN Ready)                   │
└──────────────────────────────┬────────────────────────┘
                               │
         ┌─────────────────────┴──────────────────────┐
         │ Node.js/Express API Server                 │
         │      (Single Instance)                     │
         └─────────────────────┬──────────────────────┘
                               │
         ┌─────────────────────┴──────────────────────┐
         │  MySQL 8.0+ Database                       │
         │                                            │
         └────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│    External Services Integration                    │
├─────────────────────────────────────────────────────┤
│ • Email Service (Google SMTP)                       │
│ • SMS Service (Custom Robi API)                     │
│ • File Storage (DigitalOcean Spaces)                │
└─────────────────────────────────────────────────────┘
```

---
