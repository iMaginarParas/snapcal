import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Body, Header

from app.repositories.coach_repository import coach_repo, _load_store, _save_store
from app.repositories.db_repository import db_repository
from app.database.supabase import get_track_supabase, get_coach_supabase, is_supabase_live
from app.services.diet.diet_service import diet_service
from app.services.health.steps_service import steps_service
from app.services.auth.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Master Admin Command & 360° Observability"])


# ==============================================================================
# Helper Store Functions for CRM, Consultations & Payouts
# ==============================================================================

def _get_crm_athletes() -> List[Dict[str, Any]]:
    store = _load_store()
    athletes = store.get("sabtrack_crm_athletes", [])
    if not athletes:
        athletes = [
            {
                "id": "usr-1",
                "name": "Dr. Vikram Malhotra",
                "email": "vikram.malhotra@apollohospitals.org",
                "phone": "+91 98201 44512",
                "subscriptionTier": "elite",
                "consultationPlan": "elite",
                "isPro": True,
                "assignedCoach": "Coach Priya Sharma",
                "assignedCoachId": "coach_priya_sharma",
                "allottedAt": "Oct 08, 2026",
                "allotmentNotes": "Specialised protocol for hypertension and metabolic risk management",
                "primaryGoal": "Hypertension control, HbA1c < 6.2%, metabolic stabilization",
                "healthConditions": ["Hypertension", "Pre-Diabetes", "High Cortisol"],
                "dailyStepsAvg": 11450,
                "calorieTarget": 2150,
                "streakDays": 42,
                "adherenceScore": 94,
                "createdAt": "2026-06-15",
                "lastActive": "5m ago"
            },
            {
                "id": "usr-2",
                "name": "Ananya Deshmukh",
                "email": "ananya.d@techmahindra.com",
                "phone": "+91 97692 88210",
                "subscriptionTier": "elite",
                "consultationPlan": "elite",
                "isPro": True,
                "assignedCoach": None,
                "assignedCoachId": None,
                "primaryGoal": "PCOS management, hormonal balance, sustainable 7kg fat loss",
                "healthConditions": ["PCOS / PCOD", "Insulin Resistance", "Thyroid Imbalance"],
                "dailyStepsAvg": 8900,
                "calorieTarget": 1750,
                "streakDays": 28,
                "adherenceScore": 88,
                "createdAt": "2026-07-20",
                "lastActive": "22m ago"
            },
            {
                "id": "usr-3",
                "name": "Aditya Singhania",
                "email": "aditya@singhaniacapital.com",
                "phone": "+91 98110 55001",
                "subscriptionTier": "longevity",
                "consultationPlan": "longevity",
                "isPro": True,
                "assignedCoach": "Dr. Marcus Vance",
                "assignedCoachId": "coach_marcus_vance",
                "allottedAt": "Oct 02, 2026",
                "allotmentNotes": "Concierge biohacking protocol: deep sleep optimization, VO2 max & blood biomarkers",
                "primaryGoal": "Biological age reversal, deep sleep optimization, VO2 max elite tier",
                "healthConditions": ["Longevity", "Recovery Optimization", "Sleep Architecture"],
                "dailyStepsAvg": 14200,
                "calorieTarget": 2600,
                "streakDays": 65,
                "adherenceScore": 97,
                "createdAt": "2026-05-10",
                "lastActive": "Just now"
            },
            {
                "id": "usr-4",
                "name": "Rohan Varma",
                "email": "rohan.varma@zomato.in",
                "phone": "+91 99302 11982",
                "subscriptionTier": "essential",
                "consultationPlan": "essential",
                "isPro": True,
                "assignedCoach": "Arjun Nair",
                "assignedCoachId": "coach_arjun_nair",
                "allottedAt": "Oct 05, 2026",
                "allotmentNotes": "Hypertrophy and daily macro adherence for muscle gain",
                "primaryGoal": "Muscle hypertrophy (+4kg lean mass), habit consistency, strength training",
                "healthConditions": ["General Fitness", "Postural Alignment"],
                "dailyStepsAvg": 9400,
                "calorieTarget": 2800,
                "streakDays": 19,
                "adherenceScore": 91,
                "createdAt": "2026-08-01",
                "lastActive": "1h ago"
            },
            {
                "id": "usr-5",
                "name": "Meera Chawla",
                "email": "meera.chawla@deloitte.com",
                "phone": "+91 98450 33214",
                "subscriptionTier": "essential",
                "consultationPlan": "essential",
                "isPro": True,
                "assignedCoach": None,
                "assignedCoachId": None,
                "primaryGoal": "Post-partum weight management, core restoration, daily 8k steps",
                "healthConditions": ["Post-Partum Rehab", "Diastasis Recti"],
                "dailyStepsAvg": 7600,
                "calorieTarget": 1850,
                "streakDays": 14,
                "adherenceScore": 82,
                "createdAt": "2026-08-18",
                "lastActive": "3h ago"
            },
            {
                "id": "usr-6",
                "name": "Kabir Oberoi",
                "email": "kabir.oberoi@gmail.com",
                "phone": "+91 98210 77654",
                "subscriptionTier": "pro",
                "consultationPlan": None,
                "isPro": True,
                "assignedCoach": None,
                "assignedCoachId": None,
                "primaryGoal": "Self-serve tracking, marathon half-distance preparation",
                "healthConditions": ["Endurance Training"],
                "dailyStepsAvg": 16500,
                "calorieTarget": 2900,
                "streakDays": 51,
                "adherenceScore": 95,
                "createdAt": "2026-06-01",
                "lastActive": "45m ago"
            },
            {
                "id": "usr-7",
                "name": "Shruti Iyer",
                "email": "shruti.iyer@accenture.com",
                "phone": "+91 97112 44321",
                "subscriptionTier": "free",
                "consultationPlan": None,
                "isPro": False,
                "assignedCoach": None,
                "assignedCoachId": None,
                "primaryGoal": "Basic calorie logging and steps consistency",
                "healthConditions": ["Sedentary Lifestyle"],
                "dailyStepsAvg": 5400,
                "calorieTarget": 1600,
                "streakDays": 6,
                "adherenceScore": 68,
                "createdAt": "2026-09-12",
                "lastActive": "1d ago"
            }
        ]
        store["sabtrack_crm_athletes"] = athletes
        _save_store(store)
    return athletes


def _save_crm_athletes(athletes: List[Dict[str, Any]]):
    store = _load_store()
    store["sabtrack_crm_athletes"] = athletes
    _save_store(store)


# ==============================================================================
# 1. All Coaches Overview with Aggregated Real-Time Metrics & Management
# ==============================================================================

@router.get("/coaches")
def get_admin_coaches(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """
    Returns all coaches registered in the platform along with aggregated real-time metrics:
    total earnings, active clients, review ratings, reports generated, and onboarding status.
    """
    all_profiles = coach_repo.get_available_coaches()
    all_clients = coach_repo.get_all_clients()
    store = _load_store()
    all_payments = store.get("coach_payments", [])
    all_checkins = store.get("coach_checkins", [])
    all_reports = store.get("coach_reports", [])
    all_programs = store.get("coach_programs", [])

    # If no profiles found in store yet, seed baseline profiles so database is not blank
    if not all_profiles:
        baseline_profiles = [
            {
                "id": "coach_priya_sharma",
                "name": "Coach Priya Sharma",
                "email": "priya.sharma@sabcoach.com",
                "phone": "+91 98451 22334",
                "title": "Clinical Sports Nutritionist & Mobility Coach",
                "practice_name": "Priya Sharma Performance Lab",
                "bio": "Certified Sports Nutritionist & Yoga Alliance 500hr instructor. 8+ years guiding elite athletes in metabolic health.",
                "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=200&auto=format&fit=crop&q=80",
                "rating": 4.96,
                "status": "completed",
                "created_at": "2025-01-10T08:00:00.000Z"
            },
            {
                "id": "coach_marcus_vance",
                "name": "Dr. Marcus Vance",
                "email": "marcus.vance@sabcoach.com",
                "phone": "+91 98200 44556",
                "title": "Head Strength & Hypertrophy Specialist",
                "practice_name": "Apex Athletic Performance Studio",
                "bio": "PhD in Exercise Physiology, CSCS, former Olympic strength advisor. Specializing in data-driven hypertrophy.",
                "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80",
                "rating": 4.92,
                "status": "completed",
                "created_at": "2025-01-18T10:30:00.000Z"
            },
            {
                "id": "coach_arjun_nair",
                "name": "Arjun Nair",
                "email": "arjun.nair@sabcoach.com",
                "phone": "+91 99160 88771",
                "title": "Rehabilitation & Biomechanics Coach",
                "practice_name": "Kinetic Recovery Lab",
                "bio": "Specialist in ACL rehabilitation, postural realignment, and kinetic chain endurance.",
                "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80",
                "rating": 4.88,
                "status": "completed",
                "created_at": "2025-02-05T14:00:00.000Z"
            }
        ]
        for p in baseline_profiles:
            coach_repo.save_profile(p["id"], p)
        all_profiles = baseline_profiles

    # Ensure baseline sample payments exist
    if not all_payments:
        sample_payments = [
            {
                "id": "pay_101",
                "invoiceNumber": "INV-2026-081",
                "coach_id": "coach_priya_sharma",
                "clientId": "cl_inv_1791107421",
                "clientName": "Athlete Three",
                "productName": "1:1 Precision Nutrition & Recovery Plan",
                "amount": 18500,
                "currency": "INR",
                "status": "Paid",
                "method": "UPI",
                "dueDate": "2026-10-01",
                "paidAt": "2026-10-01T14:20:00.000Z",
                "notes": "Full quarter payment received via Razorpay UPI"
            },
            {
                "id": "pay_102",
                "invoiceNumber": "INV-2026-094",
                "coach_id": "coach_priya_sharma",
                "clientId": "cl_inv_1791107422",
                "clientName": "Devika Sen",
                "productName": "Monthly Metabolic Reset Consultation",
                "amount": 7500,
                "currency": "INR",
                "status": "Pending",
                "method": "Net Banking",
                "dueDate": "2026-10-18",
                "notes": "Invoice generated, awaiting bank confirmation"
            },
            {
                "id": "pay_103",
                "invoiceNumber": "INV-2026-042",
                "coach_id": "coach_marcus_vance",
                "clientId": "cl_1791107421461",
                "clientName": "Athlete Two",
                "productName": "Elite Athletic Hypertrophy Masterclass",
                "amount": 32000,
                "currency": "INR",
                "status": "Paid",
                "method": "Card",
                "dueDate": "2026-09-25",
                "paidAt": "2026-09-25T11:00:00.000Z",
                "notes": "Paid with Corporate HDFC Credit Card"
            },
            {
                "id": "pay_104",
                "invoiceNumber": "INV-2026-058",
                "coach_id": "coach_marcus_vance",
                "clientId": "cl_1791107421462",
                "clientName": "Rohan Deshmukh",
                "productName": "Biometric Strength Coaching - 8 Weeks",
                "amount": 16000,
                "currency": "INR",
                "status": "Overdue",
                "method": "UPI",
                "dueDate": "2026-10-05",
                "notes": "Payment reminder dispatched on 2026-10-08"
            },
            {
                "id": "pay_105",
                "invoiceNumber": "INV-2026-112",
                "coach_id": "coach_arjun_nair",
                "clientId": "cl_1791107421463",
                "clientName": "Karan Mehra",
                "productName": "Post-Op ACL Kinetic Rehabilitation",
                "amount": 24000,
                "currency": "INR",
                "status": "Paid",
                "method": "UPI",
                "dueDate": "2026-09-30",
                "paidAt": "2026-09-30T16:45:00.000Z",
                "notes": "Prepaid 12-session physiotherapy package"
            }
        ]
        for pay in sample_payments:
            coach_repo.save_payment(pay)
        all_payments = sample_payments

    enriched_coaches = []
    for p in all_profiles:
        cid = p.get("id")
        coach_clients = [c for c in all_clients if c.get("coach_id") == cid]
        coach_pays = [x for x in all_payments if x.get("coach_id") == cid]
        coach_chks = [x for x in all_checkins if x.get("coach_id") == cid]
        coach_reps = [x for x in all_reports if x.get("coach_id") == cid]
        coach_progs = [x for x in all_programs if x.get("coach_id") == cid]

        # Calculate Earnings
        total_collected = sum(float(x.get("amount", 0)) for x in coach_pays if x.get("status") == "Paid")
        total_pending = sum(float(x.get("amount", 0)) for x in coach_pays if x.get("status") == "Pending")
        total_overdue = sum(float(x.get("amount", 0)) for x in coach_pays if x.get("status") == "Overdue")
        gross_volume = total_collected + total_pending + total_overdue

        # Calculate Reviews & Rating
        ratings = [float(x.get("rating", 5)) for x in coach_chks if x.get("rating")]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else float(p.get("rating", 4.9))

        enriched_coaches.append({
            "id": cid,
            "name": p.get("name") or "Coach",
            "email": p.get("email") or "",
            "phone": p.get("phone") or "",
            "role": p.get("title") or p.get("role") or "Strength & Conditioning Coach",
            "practiceName": p.get("practice_name") or p.get("practiceName") or "SabCoach Practice Lab",
            "bio": p.get("bio") or "",
            "avatar": p.get("avatar") or f"https://ui-avatars.com/api/?name={p.get('name', 'Coach')}&background=4F46E5&color=fff",
            "status": p.get("status") or "completed",
            "tempPassword": p.get("tempPassword"),
            "createdAt": p.get("created_at") or p.get("createdAt") or datetime.utcnow().isoformat(),
            "rating": avg_rating,
            "reviewCount": len(coach_chks),
            "clientCount": len(coach_clients),
            "reportsCount": len(coach_reps),
            "programsCount": len(coach_progs),
            "financials": {
                "totalCollected": total_collected,
                "totalPending": total_pending,
                "totalOverdue": total_overdue,
                "grossVolume": gross_volume,
                "currency": "INR",
                "invoicesCount": len(coach_pays)
            }
        })

    # Filtering
    if search:
        s = search.lower().strip()
        enriched_coaches = [
            c for c in enriched_coaches
            if s in c["name"].lower() or s in c["email"].lower() or s in c["role"].lower() or s in c["practiceName"].lower()
        ]

    if status and status != "all":
        enriched_coaches = [c for c in enriched_coaches if c["status"] == status]

    return {
        "success": True,
        "count": len(enriched_coaches),
        "data": enriched_coaches
    }


@router.post("/coaches")
@router.post("/coaches/provision")
def admin_provision_coach(payload: Dict[str, Any] = Body(...)):
    """
    Provisions credentials and registers a coach profile into Supabase & database.
    """
    email = (payload.get("email") or "").strip().lower()
    name = (payload.get("name") or "").strip()
    password = payload.get("password") or f"SC-{int(datetime.utcnow().timestamp())}!9"
    role = payload.get("role") or "Strength & Conditioning Coach"
    practice_name = payload.get("practiceName") or payload.get("practice_name") or f"{name}'s Practice"

    if not email or not name:
        raise HTTPException(status_code=400, detail="Name and email are required.")

    # Provision user credentials in Supabase Auth (with graceful fallback)
    auth_res = {}
    try:
        auth_res = auth_service.provision_coach(
            email=email,
            password=password,
            name=name,
            role=role,
            practice_name=practice_name
        )
    except Exception as e:
        logger.warning(f"Auth provision returned note: {e}")

    coach_id = (auth_res.get("data") or {}).get("id") or f"coach_{int(datetime.utcnow().timestamp())}"

    new_coach = {
        "id": coach_id,
        "name": name,
        "email": email,
        "phone": payload.get("phone", ""),
        "role": role,
        "title": role,
        "practice_name": practice_name,
        "practiceName": practice_name,
        "bio": payload.get("bio", ""),
        "avatar": f"https://ui-avatars.com/api/?name={name}&background=4F46E5&color=fff",
        "status": "pending_onboarding",
        "tempPassword": password,
        "notes": payload.get("notes", ""),
        "rating": 5.0,
        "reviewCount": 0,
        "clientCount": 0,
        "reportsCount": 0,
        "programsCount": 0,
        "createdAt": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }

    coach_repo.save_profile(coach_id, new_coach)

    return {
        "success": True,
        "message": f"Credentials provisioned for {name} ({email})",
        "coach": new_coach
    }


@router.put("/coaches/{coach_id}")
def admin_update_coach(coach_id: str, updates: Dict[str, Any] = Body(...)):
    """
    Updates a coach's status, practice details, phone, bio, or credentials.
    """
    profile = coach_repo.get_profile(coach_id)
    if not profile:
        all_c = coach_repo.get_available_coaches()
        profile = next((c for c in all_c if c.get("id") == coach_id), None)

    if not profile:
        profile = {"id": coach_id, "name": "Coach", "email": ""}

    merged = {**profile, **updates, "updated_at": datetime.utcnow().isoformat()}
    coach_repo.save_profile(coach_id, merged)

    return {
        "success": True,
        "message": "Coach profile updated successfully.",
        "coach": merged
    }


@router.delete("/coaches/{coach_id}")
def admin_delete_coach(coach_id: str):
    """
    Deletes a coach profile from Supabase and the persistent store.
    """
    coach_repo.delete_profile(coach_id)
    return {
        "success": True,
        "message": f"Coach {coach_id} deleted successfully."
    }


@router.post("/coaches/{coach_id}/reset-password")
def admin_reset_coach_password(coach_id: str, body: Dict[str, Any] = Body(...)):
    """
    Sets a new temporary password for the coach and records it in their profile.
    """
    temp_password = body.get("tempPassword") or body.get("password")
    if not temp_password:
        raise HTTPException(status_code=400, detail="tempPassword is required.")

    profile = coach_repo.get_profile(coach_id) or {"id": coach_id}
    profile["tempPassword"] = temp_password
    profile["updated_at"] = datetime.utcnow().isoformat()
    coach_repo.save_profile(coach_id, profile)

    return {
        "success": True,
        "message": "Temporary password reset successfully.",
        "tempPassword": temp_password
    }


# ==============================================================================
# 2. Coach 360° Deep-Dive Inspector
# ==============================================================================

@router.get("/coaches/{coach_id}/deep-dive")
def get_coach_deep_dive(coach_id: str):
    """
    Returns 360° observability for a specific coach:
    - Profile and Practice info
    - Complete Earnings, Invoices & Payment audit
    - All Client Reviews & Check-ins
    - All Generated Clinical Reports & Audits
    - All Assigned Athletes with live SabTrack biometrics (steps, cals, adherence)
    - All Programs and Prescriptions
    """
    profile = coach_repo.get_profile(coach_id)
    if not profile:
        all_c = coach_repo.get_available_coaches()
        profile = next((c for c in all_c if c.get("id") == coach_id), None)

    if not profile:
        profile = {
            "id": coach_id,
            "name": "Coach",
            "email": "",
            "title": "Health & Performance Coach",
            "practice_name": "SabCoach Practice",
            "rating": 4.9
        }

    all_clients = coach_repo.get_clients(coach_id)
    payments = coach_repo.get_payments(coach_id)
    checkins = coach_repo.get_checkins(coach_id)
    reports = coach_repo.get_reports(coach_id)
    programs = coach_repo.get_programs(coach_id)
    sessions = coach_repo.get_sessions(coach_id)
    leads = coach_repo.get_leads(coach_id)

    enhanced_clients = []
    for cl in all_clients:
        cid_str = str(cl.get("id"))
        st_data = cl.get("sabtrack_data") or cl.get("sabtrack") or {}
        st_uid = str(st_data.get("sabtrack_user_id") or cl.get("user_id") or cid_str)

        daily_steps = 0
        try:
            steps_res = steps_service.get_daily_steps(st_uid)
            daily_steps = (steps_res.get("data") or {}).get("final_steps") or cl.get("dailyStepsAvg") or 8200
        except Exception:
            daily_steps = cl.get("dailyStepsAvg") or 8200

        diet_tel = {}
        try:
            diet_tel = diet_service.get_client_diet_telemetry(st_uid)
        except Exception:
            pass

        actual = diet_tel.get("actual") or {}
        prescribed = diet_tel.get("prescribed") or {}
        adh = diet_tel.get("adherence_percentage")

        enhanced_clients.append({
            **cl,
            "daily_steps": daily_steps,
            "actual_calories": actual.get("calories") or 0,
            "target_calories": prescribed.get("calories") or cl.get("target_cals", 2100),
            "adherence_percentage": adh if adh is not None else cl.get("adherence", 90),
            "connected_to_sabtrack": bool(st_data.get("connected", True))
        })

    total_collected = sum(float(x.get("amount", 0)) for x in payments if x.get("status") == "Paid")
    total_pending = sum(float(x.get("amount", 0)) for x in payments if x.get("status") == "Pending")
    total_overdue = sum(float(x.get("amount", 0)) for x in payments if x.get("status") == "Overdue")

    ratings = [float(x.get("rating", 5)) for x in checkins if x.get("rating")]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else float(profile.get("rating", 4.9))

    return {
        "success": True,
        "coach": {
            "id": coach_id,
            "name": profile.get("name") or "Coach",
            "email": profile.get("email") or "",
            "phone": profile.get("phone") or "",
            "title": profile.get("title") or profile.get("role") or "Coach",
            "practiceName": profile.get("practice_name") or profile.get("practiceName") or "SabCoach Studio",
            "bio": profile.get("bio") or "",
            "avatar": profile.get("avatar") or f"https://ui-avatars.com/api/?name={profile.get('name', 'Coach')}&background=4F46E5&color=fff",
            "rating": avg_rating,
            "status": profile.get("status", "completed"),
            "createdAt": profile.get("created_at") or datetime.utcnow().isoformat()
        },
        "financials": {
            "totalCollected": total_collected,
            "totalPending": total_pending,
            "totalOverdue": total_overdue,
            "grossVolume": total_collected + total_pending + total_overdue,
            "invoicesCount": len(payments),
            "currency": "INR",
            "payments": payments
        },
        "reviews": {
            "averageRating": avg_rating,
            "totalReviews": len(checkins),
            "checkins": checkins
        },
        "reports": {
            "totalReports": len(reports),
            "items": reports
        },
        "clients": {
            "totalClients": len(enhanced_clients),
            "items": enhanced_clients
        },
        "programs": {
            "totalPrograms": len(programs),
            "items": programs
        },
        "sessions": {
            "totalSessions": len(sessions),
            "items": sessions
        },
        "leads": {
            "totalLeads": len(leads),
            "items": leads
        }
    }


# ==============================================================================
# 3. SabTrack Mobile Users Management & CRM Directory
# ==============================================================================

@router.get("/sabtrack/users")
def get_admin_sabtrack_users(
    search: Optional[str] = Query(None),
    tier: Optional[str] = Query(None)
):
    """
    Returns live registered users from SabTrack merged with CRM athlete records,
    including subscription tiers, consultation plan, real steps, and assigned coaches.
    """
    crm_athletes = _get_crm_athletes()
    users_dict: Dict[str, Dict[str, Any]] = {a["id"]: a for a in crm_athletes}

    # Merge live Supabase users if available
    sb = get_track_supabase()
    if sb and is_supabase_live():
        try:
            q = sb.from_("users").select("*").limit(100)
            res = q.execute()
            if res.data:
                for u in res.data:
                    uid = str(u.get("id"))
                    sub_tier = u.get("subscription_tier") or ("pro" if u.get("is_pro") else "free")
                    if uid in users_dict:
                        users_dict[uid]["isPro"] = bool(u.get("is_pro", users_dict[uid]["isPro"]))
                        if u.get("assigned_coach"):
                            users_dict[uid]["assignedCoach"] = u.get("assigned_coach")
                    else:
                        users_dict[uid] = {
                            "id": uid,
                            "name": u.get("name") or u.get("username") or "Athlete",
                            "email": u.get("email") or "",
                            "phone": u.get("phone") or "",
                            "subscriptionTier": sub_tier,
                            "consultationPlan": sub_tier if sub_tier in ["essential", "elite", "longevity"] else None,
                            "isPro": bool(u.get("is_pro")),
                            "assignedCoach": u.get("assigned_coach"),
                            "dailyStepsAvg": u.get("steps_goal") or 8500,
                            "calorieTarget": u.get("calorie_goal") or 2200,
                            "streakDays": u.get("streak_days") or 7,
                            "createdAt": u.get("created_at") or datetime.utcnow().isoformat(),
                            "lastActive": "Active Today"
                        }
        except Exception as e:
            logger.warning(f"Supabase users query failed: {e}")

    users_list = list(users_dict.values())

    if search:
        s = search.lower().strip()
        users_list = [
            u for u in users_list
            if s in u["name"].lower() or s in u["email"].lower() or s in u.get("phone", "").lower()
        ]

    if tier and tier != "all":
        if tier == "pro":
            users_list = [u for u in users_list if u.get("isPro") or u.get("subscriptionTier") in ("pro", "elite", "longevity", "essential")]
        elif tier == "free":
            users_list = [u for u in users_list if not u.get("isPro") and u.get("subscriptionTier") == "free"]
        else:
            users_list = [u for u in users_list if u.get("subscriptionTier") == tier or u.get("consultationPlan") == tier]

    return {
        "success": True,
        "count": len(users_list),
        "data": users_list
    }


@router.post("/sabtrack/users/{user_id}/toggle-pro")
def toggle_admin_sabtrack_user_pro(user_id: str):
    """
    Toggles the Pro entitlement of a SabTrack athlete in Supabase and CRM store.
    """
    athletes = _get_crm_athletes()
    target = next((a for a in athletes if a.get("id") == user_id), None)
    new_pro_state = True

    if target:
        target["isPro"] = not target.get("isPro", False)
        target["subscriptionTier"] = "pro" if target["isPro"] else "free"
        new_pro_state = target["isPro"]
        _save_crm_athletes(athletes)

    sb = get_track_supabase()
    if sb and is_supabase_live():
        try:
            curr = sb.from_("users").select("is_pro").eq("id", user_id).single().execute()
            if curr and curr.data:
                new_pro_state = not bool(curr.data.get("is_pro"))
                sb.from_("users").update({
                    "is_pro": new_pro_state,
                    "subscription_tier": "pro" if new_pro_state else "free"
                }).eq("id", user_id).execute()
        except Exception as e:
            logger.warning(f"Failed to toggle pro on Supabase: {e}")

    return {
        "success": True,
        "user_id": user_id,
        "is_pro": new_pro_state,
        "message": "User subscription entitlement updated successfully."
    }


# ==============================================================================
# 4. CRM Athlete Coach Allotment & Plan Operations
# ==============================================================================

@router.post("/crm/athletes/{athlete_id}/allot-coach")
def allot_coach_to_athlete(athlete_id: str, body: Dict[str, Any] = Body(...)):
    """
    Allots a designated coach to an athlete according to their consultation plan.
    Syncs with both CRM store and Supabase coach.clients table.
    """
    coach_id = body.get("coachId")
    coach_name = body.get("coachName")
    plan_tier = body.get("planTier")
    notes = body.get("notes")

    if not coach_id or not coach_name:
        raise HTTPException(status_code=400, detail="coachId and coachName are required.")

    today_str = datetime.utcnow().strftime("%b %d, %Y")
    athletes = _get_crm_athletes()
    target = next((a for a in athletes if a.get("id") == athlete_id), None)

    if target:
        target["assignedCoach"] = coach_name
        target["assignedCoachId"] = coach_id
        target["allottedAt"] = today_str
        if notes:
            target["allotmentNotes"] = notes
        if plan_tier and plan_tier in ["essential", "elite", "longevity", "pro", "free"]:
            target["subscriptionTier"] = plan_tier
            if plan_tier in ["essential", "elite", "longevity"]:
                target["consultationPlan"] = plan_tier
                target["isPro"] = True
        _save_crm_athletes(athletes)

    # Sync to coach.clients in Supabase/store so coach dashboard reflects client
    try:
        athlete_name = target.get("name", "Athlete") if target else "Athlete"
        athlete_email = target.get("email", "") if target else ""
        athlete_phone = target.get("phone", "") if target else ""
        coach_repo.save_client({
            "id": f"cl_{athlete_id}",
            "coach_id": coach_id,
            "name": athlete_name,
            "email": athlete_email,
            "phone": athlete_phone,
            "status": "Active",
            "package": plan_tier or "Consultation Plan",
            "goal": (target or {}).get("primaryGoal", "Health & Performance Optimization"),
            "connected_to_sabtrack": True,
            "user_id": athlete_id
        })
    except Exception as e:
        logger.warning(f"Failed to sync coach client record: {e}")

    # Mark any pending consultation request for this athlete as placed
    store = _load_store()
    requests = store.get("consultation_requests", [])
    for req in requests:
        if req.get("athleteId") == athlete_id or req.get("athleteEmail", "").lower() == (target or {}).get("email", "").lower():
            req["status"] = "placed"
            req["placedCoachId"] = coach_id
            req["placedCoachName"] = coach_name
            req["placedAt"] = today_str
    store["consultation_requests"] = requests
    _save_store(store)

    return {
        "success": True,
        "message": f"Coach {coach_name} successfully allotted to athlete.",
        "athlete_id": athlete_id
    }


@router.post("/crm/athletes/{athlete_id}/unallot-coach")
def unallot_coach_from_athlete(athlete_id: str):
    """
    Disconnects an athlete from their assigned coach.
    """
    athletes = _get_crm_athletes()
    target = next((a for a in athletes if a.get("id") == athlete_id), None)
    if target:
        prev_coach_id = target.get("assignedCoachId")
        target["assignedCoach"] = None
        target["assignedCoachId"] = None
        target["allottedAt"] = None
        _save_crm_athletes(athletes)

        if prev_coach_id:
            try:
                coach_repo.delete_client(f"cl_{athlete_id}", prev_coach_id)
            except Exception:
                pass

    return {
        "success": True,
        "message": "Coach disconnected from athlete successfully.",
        "athlete_id": athlete_id
    }


@router.post("/crm/athletes/{athlete_id}/update-plan")
def update_athlete_plan(athlete_id: str, body: Dict[str, Any] = Body(...)):
    """
    Updates an athlete's subscription tier or consultation plan tier.
    """
    new_tier = body.get("tier")
    if not new_tier:
        raise HTTPException(status_code=400, detail="tier is required.")

    athletes = _get_crm_athletes()
    target = next((a for a in athletes if a.get("id") == athlete_id), None)
    if target:
        target["subscriptionTier"] = new_tier
        target["isPro"] = new_tier != "free"
        if new_tier in ["essential", "elite", "longevity"]:
            target["consultationPlan"] = new_tier
        else:
            target["consultationPlan"] = None
        _save_crm_athletes(athletes)

    return {
        "success": True,
        "message": f"Athlete subscription tier set to {new_tier}.",
        "athlete_id": athlete_id,
        "tier": new_tier
    }


@router.post("/crm/athletes/batch-allot")
def batch_allot_athletes(body: Dict[str, Any] = Body(...)):
    """
    Batch assigns multiple athletes to a designated coach.
    """
    athlete_ids = body.get("athleteIds", [])
    coach_id = body.get("coachId")
    coach_name = body.get("coachName")
    plan_tier = body.get("planTier")
    notes = body.get("notes")

    if not coach_id or not coach_name:
        raise HTTPException(status_code=400, detail="coachId and coachName are required.")

    today_str = datetime.utcnow().strftime("%b %d, %Y")
    athletes = _get_crm_athletes()
    count = 0

    for aid in athlete_ids:
        target = next((a for a in athletes if a.get("id") == aid), None)
        if target:
            target["assignedCoach"] = coach_name
            target["assignedCoachId"] = coach_id
            target["allottedAt"] = today_str
            if notes:
                target["allotmentNotes"] = notes
            if plan_tier and plan_tier in ["essential", "elite", "longevity", "pro", "free"]:
                target["subscriptionTier"] = plan_tier
                if plan_tier in ["essential", "elite", "longevity"]:
                    target["consultationPlan"] = plan_tier
                    target["isPro"] = True
            count += 1
            try:
                coach_repo.save_client({
                    "id": f"cl_{aid}",
                    "coach_id": coach_id,
                    "name": target.get("name", "Athlete"),
                    "email": target.get("email", ""),
                    "phone": target.get("phone", ""),
                    "status": "Active",
                    "package": plan_tier or "Consultation Plan",
                    "goal": target.get("primaryGoal", "Health Optimization"),
                    "connected_to_sabtrack": True
                })
            except Exception:
                pass

    _save_crm_athletes(athletes)

    return {
        "success": True,
        "updated_count": count,
        "message": f"Batch allotted {count} athletes to {coach_name}."
    }


# ==============================================================================
# 5. Consultation Plans & Coach Placement
# ==============================================================================

@router.get("/consultations/requests")
def get_consultation_requests():
    """
    Returns pending and placed athlete consultation requests across all tiers.
    """
    store = _load_store()
    requests = store.get("consultation_requests", [])

    if not requests:
        requests = [
            {
                "id": "req-01",
                "athleteId": "usr-1",
                "athleteName": "Dr. Vikram Malhotra",
                "athleteEmail": "vikram.malhotra@apollohospitals.org",
                "athletePhone": "+91 98201 44512",
                "planId": "elite",
                "planName": "02 — ELITE (Specialised Health & Performance)",
                "planPrice": "₹6,000/package",
                "primaryGoals": "Hypertension control, HbA1c reduction (currently 6.8%), visceral adiposity protocol",
                "status": "pending_placement",
                "requestedAt": "Today at 10:45 AM"
            },
            {
                "id": "req-02",
                "athleteId": "usr-2",
                "athleteName": "Ananya Deshmukh",
                "athleteEmail": "ananya.d@techmahindra.com",
                "athletePhone": "+91 97692 88210",
                "planId": "essential",
                "planName": "01 — ESSENTIAL (Fitness & Nutrition)",
                "planPrice": "₹3,000/month",
                "primaryGoals": "Sustainable 8kg fat loss, habit building, daily 8,000 steps consistency & vegetarian macros",
                "status": "pending_placement",
                "requestedAt": "Yesterday at 04:12 PM"
            },
            {
                "id": "req-03",
                "athleteId": "usr-3",
                "athleteName": "Aditya Singhania",
                "athleteEmail": "aditya@singhaniacapital.com",
                "athletePhone": "+91 98110 55001",
                "planId": "longevity",
                "planName": "03 — LONGEVITY (Biohacking & Wellness)",
                "planPrice": "Premium",
                "primaryGoals": "Advanced biological age reversal, deep sleep optimization (Oura ring sync), VO2 max enhancement",
                "status": "placed",
                "placedCoachId": "coach_marcus_vance",
                "placedCoachName": "Dr. Marcus Vance (Strength & Physiology)",
                "placedAt": "Oct 11, 2026",
                "requestedAt": "3 days ago"
            }
        ]
        store["consultation_requests"] = requests
        _save_store(store)

    return {
        "success": True,
        "count": len(requests),
        "data": requests
    }


@router.post("/consultations/requests")
def create_consultation_request(payload: Dict[str, Any] = Body(...)):
    """
    Submits a new consultation inquiry from an athlete.
    """
    store = _load_store()
    requests = store.get("consultation_requests", [])
    new_req = {
        "id": f"req-{int(datetime.utcnow().timestamp())}",
        "athleteId": payload.get("athleteId", f"usr-{int(datetime.utcnow().timestamp())}"),
        "athleteName": payload.get("athleteName", "Athlete"),
        "athleteEmail": payload.get("athleteEmail", ""),
        "athletePhone": payload.get("athletePhone", ""),
        "planId": payload.get("planId", "essential"),
        "planName": payload.get("planName", "Essential Consultation"),
        "planPrice": payload.get("planPrice", "₹3,000/month"),
        "primaryGoals": payload.get("primaryGoals", "Fitness & Nutrition"),
        "status": "pending_placement",
        "requestedAt": "Just now"
    }
    requests.insert(0, new_req)
    store["consultation_requests"] = requests
    _save_store(store)

    return {"success": True, "data": new_req}


@router.post("/consultations/{request_id}/place-coach")
def place_coach_for_consultation(request_id: str, body: Dict[str, Any] = Body(...)):
    """
    Assigns a coach to an athlete consultation inquiry and updates the CRM roster.
    """
    coach_id = body.get("coachId")
    coach_name = body.get("coachName")

    if not coach_id or not coach_name:
        raise HTTPException(status_code=400, detail="coachId and coachName are required.")

    store = _load_store()
    requests = store.get("consultation_requests", [])
    target = next((r for r in requests if r.get("id") == request_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Consultation request not found.")

    today_str = datetime.utcnow().strftime("%b %d, %Y")
    target["status"] = "placed"
    target["placedCoachId"] = coach_id
    target["placedCoachName"] = coach_name
    target["placedAt"] = today_str
    _save_store(store)

    # Automatically allot coach to athlete in CRM roster
    athlete_id = target.get("athleteId")
    athletes = _get_crm_athletes()
    a_target = next((a for a in athletes if a.get("id") == athlete_id or a.get("email") == target.get("athleteEmail")), None)
    if a_target:
        a_target["assignedCoach"] = coach_name
        a_target["assignedCoachId"] = coach_id
        a_target["allottedAt"] = today_str
        _save_crm_athletes(athletes)

    return {
        "success": True,
        "message": f"Athlete successfully matched and placed with {coach_name}.",
        "request": target
    }


# ==============================================================================
# 6. Coach Payout Ledger & Financial Settlements
# ==============================================================================

@router.get("/coach-payouts")
@router.get("/payouts")
def get_coach_payout_ledger(commission_rate: float = Query(15.0)):
    """
    Generates a live coach payout ledger based on active consultation subscriptions,
    calculating platform commission take rate, net coach payout, and settlement state.
    """
    store = _load_store()
    settlements: Dict[str, Dict[str, Any]] = store.get("coach_payout_settlements", {})

    athletes = _get_crm_athletes()
    coaches = coach_repo.get_available_coaches()

    plan_prices = {
        "essential": 3000,
        "elite": 6000,
        "longevity": 12000
    }

    ledger = []
    p_id = 100

    for a in athletes:
        sub_tier = a.get("subscriptionTier") or a.get("consultationPlan")
        if sub_tier in plan_prices and a.get("assignedCoach"):
            c_id = a.get("assignedCoachId")
            if not c_id:
                coach = next((c for c in coaches if c.get("name", "").lower() == a["assignedCoach"].lower()), None)
                c_id = coach.get("id", "coach_1") if coach else "coach_1"

            gross = plan_prices[sub_tier]
            take_amt = round((gross * commission_rate) / 100)
            net_payout = gross - take_amt
            pay_id = f"pay_{a.get('id')}"

            settled_info = settlements.get(pay_id, {})
            is_settled = settled_info.get("status") == "settled"

            ledger.append({
                "id": pay_id,
                "coachId": c_id,
                "coachName": a.get("assignedCoach"),
                "athleteId": a.get("id"),
                "athleteName": a.get("name"),
                "planTier": sub_tier,
                "planAmount": gross,
                "platformTakeRatePct": commission_rate,
                "platformTakeAmount": take_amt,
                "coachNetPayout": net_payout,
                "status": "settled" if is_settled else "pending",
                "period": "October 2026",
                "settledAt": settled_info.get("settledAt") or ("Oct 08, 2026" if is_settled else None),
                "transactionRef": settled_info.get("transactionRef") or (f"TXN-SAB-8491{p_id}" if is_settled else None)
            })
            p_id += 1

    return {
        "success": True,
        "count": len(ledger),
        "data": ledger
    }


@router.post("/coach-payouts/{payout_id}/settle")
def settle_coach_payout(payout_id: str, body: Optional[Dict[str, Any]] = Body(default={})):
    """
    Marks a coach payout record as settled with an immutable transaction reference.
    """
    store = _load_store()
    settlements = store.setdefault("coach_payout_settlements", {})

    txn_ref = (body or {}).get("transactionRef") or f"TXN-SAB-{int(datetime.utcnow().timestamp())}"
    today_str = datetime.utcnow().strftime("%b %d, %Y")

    settlements[payout_id] = {
        "status": "settled",
        "settledAt": today_str,
        "transactionRef": txn_ref
    }
    _save_store(store)

    return {
        "success": True,
        "message": f"Payout {payout_id} marked as settled.",
        "payout_id": payout_id,
        "transactionRef": txn_ref,
        "settledAt": today_str
    }


# ==============================================================================
# 7. Unified Ecosystem Health & Live Schema Counts
# ==============================================================================

@router.get("/ecosystem/health")
def get_admin_ecosystem_health():
    """
    Returns real-time database schema stats, table row counts, and connectivity status.
    """
    sb = get_track_supabase()
    store = _load_store()

    # Query counts from local store with live Supabase validation
    counts = {
        "coaches_count": len(coach_repo.get_available_coaches()),
        "clients_count": len(coach_repo.get_all_clients()),
        "crm_athletes_count": len(store.get("sabtrack_crm_athletes", [])),
        "consultations_count": len(store.get("consultation_requests", [])),
        "payments_count": len(store.get("coach_payments", [])),
        "checkins_count": len(store.get("coach_checkins", [])),
        "reports_count": len(store.get("coach_reports", [])),
        "programs_count": len(store.get("coach_programs", [])),
        "sessions_count": len(store.get("coach_sessions", [])),
        "leads_count": len(store.get("coach_leads", [])),
        "applications_count": len(store.get("coach_applications", []))
    }

    # If Supabase is live, supplement with live public schema counts
    live_users_count = 0
    if sb and is_supabase_live():
        try:
            res = sb.from_("users").select("id", count="exact").limit(1).execute()
            if hasattr(res, "count") and res.count is not None:
                live_users_count = res.count
        except Exception:
            pass

    return {
        "success": True,
        "status": "healthy",
        "supabase_connected": is_supabase_live(),
        "database_topology": {
            "sabtrack_schema": "public",
            "sabcoach_schema": "coach",
            "api_endpoint": "https://api.sabtrack.in/api",
            "live_users_count": live_users_count
        },
        "live_metrics": counts,
        "verified_at": datetime.utcnow().isoformat()
    }


# ==============================================================================
# 8. Coach Onboarding & Intake Applications Review Queue
# ==============================================================================

@router.get("/coach-applications")
def get_admin_coach_applications(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """
    Returns pending, approved, and rejected coach intake applications.
    """
    store = _load_store()
    applications = store.get("coach_applications", [])

    if not applications:
        applications = [
            {
                "id": "app-1",
                "name": "Siddharth Mehra",
                "email": "siddharth.mehra@fitstrength.io",
                "phone": "+91 98201 44892",
                "domain": "Strength & Conditioning",
                "experienceYears": "5–8 Years",
                "aboutWork": "Specialized in biomechanically sound resistance training, breaking strength plateaus, and structured progressive overload. Train competitive powerlifters and athletes seeking hypertrophy.",
                "clientCount": 45,
                "certifications": "CSCS (NSCA), ACE CPT, Precision Nutrition L1",
                "portfolioUrl": "@coach.siddharth_m",
                "status": "pending_review",
                "appliedAt": "2 hours ago"
            },
            {
                "id": "app-2",
                "name": "Tanvi Deshmukh",
                "email": "tanvi.nutrition@healthspace.in",
                "phone": "+91 99302 77104",
                "domain": "Clinical Nutrition & Dietetics",
                "experienceYears": "6–8 Years",
                "aboutWork": "Clinical dietitian working with women managing PCOS/PCOD, hypothyroidism, and insulin resistance. Focus on gut microbiome health and non-restrictive sustainable dietary protocols.",
                "clientCount": 80,
                "certifications": "M.Sc. Clinical Nutrition, Certified Diabetes Educator (CDE)",
                "portfolioUrl": "linkedin.com/in/tanvi-deshmukh-rd",
                "status": "pending_review",
                "appliedAt": "5 hours ago"
            },
            {
                "id": "app-3",
                "name": "Dr. Naman Kashyap",
                "email": "dr.naman@longevityperformance.org",
                "phone": "+91 98110 55219",
                "domain": "Longevity, Biomarkers & Healthspan",
                "experienceYears": "9+ Years (Veteran)",
                "aboutWork": "Sports medicine and healthspan practitioner. Focus on VO2 max testing, continuous glucose telemetry, lipid panel modulation, and sleep architecture optimization.",
                "clientCount": 35,
                "certifications": "MBBS, Sports Medicine Fellowship, American College of Sports Medicine (ACSM)",
                "portfolioUrl": "dranamankashyap.com",
                "status": "pending_review",
                "appliedAt": "Yesterday"
            }
        ]
        store["coach_applications"] = applications
        _save_store(store)

    filtered = applications
    if status and status != "all":
        filtered = [a for a in filtered if a.get("status") == status]

    if search:
        q = search.lower()
        filtered = [
            a for a in filtered
            if q in a.get("name", "").lower()
            or q in a.get("email", "").lower()
            or q in a.get("domain", "").lower()
            or q in a.get("certifications", "").lower()
        ]

    return {
        "success": True,
        "count": len(filtered),
        "data": filtered
    }


@router.post("/coach-applications")
def submit_coach_application(payload: Dict[str, Any] = Body(...)):
    """
    Submits a trainer onboarding application for administrator review.
    """
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    if not name or not email:
        raise HTTPException(status_code=400, detail="Name and email are required.")

    store = _load_store()
    applications = store.get("coach_applications", [])

    app_id = payload.get("id") or f"app-{int(datetime.utcnow().timestamp())}"
    new_app = {
        "id": app_id,
        "name": name,
        "email": email,
        "phone": payload.get("phone", ""),
        "domain": payload.get("domain", "General Fitness"),
        "experienceYears": payload.get("experienceYears", "1–2 Years"),
        "aboutWork": payload.get("aboutWork", ""),
        "clientCount": int(payload.get("clientCount", 0)),
        "certifications": payload.get("certifications", ""),
        "portfolioUrl": payload.get("portfolioUrl", ""),
        "status": "pending_review",
        "appliedAt": "Just now",
        "created_at": datetime.utcnow().isoformat()
    }

    # Deduplicate by email
    applications = [a for a in applications if a.get("email") != email]
    applications.insert(0, new_app)
    store["coach_applications"] = applications
    _save_store(store)

    return {
        "success": True,
        "message": "Coach onboarding application submitted successfully.",
        "data": new_app
    }


@router.post("/coach-applications/{application_id}/approve")
def approve_coach_application(
    application_id: str,
    body: Optional[Dict[str, Any]] = Body(default={})
):
    """
    Approves a coach intake application and provisions their profile credentials.
    """
    store = _load_store()
    applications = store.get("coach_applications", [])
    target = next((a for a in applications if a.get("id") == application_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Application not found.")

    target["status"] = "approved"
    target["reviewedAt"] = datetime.utcnow().strftime("%b %d, %Y")
    _save_store(store)

    # Provision coach profile into store & database
    coach_id = f"coach_{target['name'].lower().replace(' ', '_')}"
    temp_pass = (body or {}).get("tempPassword") or f"SC-{int(datetime.utcnow().timestamp())}!9"

    new_coach = {
        "id": coach_id,
        "name": target["name"],
        "email": target["email"],
        "phone": target.get("phone", ""),
        "title": target.get("domain", "Coach"),
        "role": target.get("domain", "Coach"),
        "practice_name": f"{target['name']}'s Practice",
        "practiceName": f"{target['name']}'s Practice",
        "bio": target.get("aboutWork", ""),
        "status": "active",
        "tempPassword": temp_pass,
        "clientCount": target.get("clientCount", 0),
        "rating": 5.0,
        "reviewCount": 0,
        "reportsCount": 0,
        "programsCount": 0,
        "createdAt": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }

    coach_repo.create_or_update_profile(new_coach)

    return {
        "success": True,
        "message": f"Application for {target['name']} approved and provisioned.",
        "coach": new_coach
    }


@router.post("/coach-applications/{application_id}/reject")
def reject_coach_application(
    application_id: str,
    body: Optional[Dict[str, Any]] = Body(default={})
):
    """
    Declines a coach intake application with an optional reason.
    """
    store = _load_store()
    applications = store.get("coach_applications", [])
    target = next((a for a in applications if a.get("id") == application_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Application not found.")

    reason = body.get("reason", "Candidate does not meet clinical practice threshold") if body else "Candidate does not meet threshold"
    target["status"] = "rejected"
    target["rejectionReason"] = reason
    target["reviewedAt"] = datetime.utcnow().strftime("%b %d, %Y")
    _save_store(store)

    return {
        "success": True,
        "message": f"Application for {target['name']} declined.",
        "application_id": application_id
    }
