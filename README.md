# Automated Online Student Clearance System

## Using Two-Factor Verification Protocol

A web-based student clearance management system designed to automate and improve the university clearance process through centralized clearance tracking, document submission, role-based workflow management, notifications, rejection feedback, administrative reporting, and stage-specific One-Time Password (OTP) verification.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Objectives](#objectives)
- [Key Features](#key-features)
- [System Users](#system-users)
- [Clearance Workflow](#clearance-workflow)
- [Two-Factor Verification](#two-factor-verification)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Security Considerations](#security-considerations)
- [Project Scope](#project-scope)
- [Limitations](#limitations)
- [Screenshots](#screenshots)
- [Documentation](#documentation)
- [Contributors](#contributors)
- [Supervisor](#supervisor)
- [License](#license)

---

## Overview

The Automated Online Student Clearance System is a web-based application designed to improve the student clearance process by replacing fragmented manual activities with a centralized digital workflow.

The system allows students to submit clearance information and documents online, monitor their clearance progress, receive notifications, respond to rejection feedback, and progress through clearance stages using stage-specific OTP verification.

Clearance officers can review submissions, approve or reject requests, provide feedback, update clearance status, and control progression to subsequent stages.

Administrators can monitor clearance activities, manage users, view system-wide information, and generate reports.

The system was developed as an academic project within the Department of Computer Science, Faculty of Physical Sciences, University of Nigeria, Nsukka.

---

## Problem Statement

Traditional student clearance processes can require students to move between multiple offices to obtain approvals, submit documents, and obtain signatures.

This creates challenges including:

- Long processing times
- Physical queues and repeated office visits
- Document misplacement
- Limited visibility into clearance progress
- Poor communication between students and clearance officers
- Inadequate rejection feedback
- Limited administrative monitoring
- Weak control over progression between clearance stages

This project addresses these challenges through an integrated web-based clearance management system.

---

## Objectives

The system is designed to:

1. Provide real-time clearance tracking.
2. Provide an administrative dashboard for monitoring clearance activities.
3. Send email notifications for important clearance events.
4. Provide clear rejection feedback to students.
5. Implement stage-specific OTP verification for controlled progression between clearance stages.
6. Support centralized management of clearance activities.
7. Generate administrative reports.

---

## Key Features

### Student

- Account registration and authentication
- Secure login
- Clearance submission
- Document upload
- Clearance progress tracking
- Clearance status monitoring
- Rejection feedback
- Email notifications
- OTP verification
- Support/complaint submission

### Clearance Officer

- Officer authentication
- View student clearance requests
- Review submitted documents
- Approve clearance requests
- Reject clearance requests
- Provide rejection feedback
- Update clearance status
- Generate stage-specific OTP verification
- Monitor assigned clearance stages

### Administrator

- Administrative dashboard
- User management
- Clearance monitoring
- Department/workflow management
- Report generation
- System activity monitoring
- Audit information

---

## Clearance Workflow

The system models the student clearance process as a sequence of stages.

A student completes the requirements for the current stage and submits the required information or documents.

The responsible clearance officer reviews the submission.

The officer may:

- Approve the submission
- Reject the submission
- Provide feedback requiring correction

After successful approval, the system generates a stage-specific OTP.

The student must successfully verify the OTP before proceeding to the next clearance stage.

This prevents unrestricted progression through the workflow.

---

## Two-Factor Verification

The system implements a stage-based Two-Factor Verification Protocol using One-Time Passwords (OTP).

The OTP mechanism is used to verify a student's eligibility to progress from one completed clearance stage to the next.

### Workflow

```text
Student submits clearance
        |
        v
Officer reviews submission
        |
   +----+----+
   |         |
Reject     Approve
   |         |
   v         v
Feedback   Generate OTP
   |         |
   |         v
   |    Student enters OTP
   |         |
   |    +----+----+
   |    |         |
   |  Invalid   Valid
   |    |         |
   |    v         v
   |  Remain    Next Stage
   |  at stage
   |
Resubmit
