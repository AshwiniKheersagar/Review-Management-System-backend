from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel # data validation
from app.models.user import init_db  
from datetime import datetime
from app.utils.auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict 
from fastapi import Query,Body

from app.controllers.Authentication.auth_controller import login_user, create_user
from app.controllers.Feedback.FeedbackForm import (submit_feedback,update_feedback_db,delete_feedback)

from app.controllers.Team.team_controller import (get_unassigned_employees,get_manager_teams,remove_team_member,add_team_member);

from app.controllers.Feedback.Feedback_Acknowledge import(acknowledge_feedback,
    get_feedback_acknowledgment);

from app.controllers.Feedback.Feedback_History import (get_employee_details,get_employee_feedback,get_feedback_history)

from app.controllers.Dashboard.employee_controller import(get_employee_dashboard_stats,get_employee_feedback_timeline)

from app.controllers.Dashboard.manager_controller import (get_feedback_trends,get_manager_dashboard_overview,get_team_member_stats)



app = FastAPI()
init_db()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your React app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- Schemas -----------
class LoginInput(BaseModel):
    email: str
    password: str

class RegisterInput(BaseModel):
    name: str
    email: str
    password: str
    role: str = "employee"  # Default role


class FeedbackResponse(BaseModel):
    id:int
    manager_id:int
    employee_id:int
    strengths:str
    areas_to_improve:str
    sentiment:str
    rating:int
    created_at:datetime

class TeamCreate(BaseModel):
    employee_email: str

class FeedbackAcknowledge(BaseModel):
    comment: Optional[str] = None

class FeedbackAcknowledgeResponse(BaseModel):
    id: int
    feedback_id: int
    employee_id: int
    acknowledged_at: datetime
    comment: Optional[str]
    employee_name: str

class TeamMemberResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    assigned_at: datetime
    feedback_count: int

class FeedbackCreate(BaseModel):
    employee_id: str
    strengths: str
    areas_to_improve: str
    sentiment: str
    rating: int

class FeedbackUpdate(BaseModel):
    strengths: str
    areas_to_improve: str
    sentiment: str
    rating: int

class EmployeeDashboardStats(BaseModel):
    total_feedback: int
    avg_rating: float
    positive_count: int
    acknowledged_count: int
    recent_feedback: List[FeedbackResponse]

class FeedbackTimelineResponse(BaseModel):
    id: int
    strengths: str
    areas_to_improve: str
    sentiment: str
    rating: int
    created_at: datetime
    is_acknowledged: bool
    manager_name: str
    acknowledgment_comment: Optional[str] = None

class TeamOverviewStats(BaseModel):
    team_size: int
    total_feedback_given: int
    avg_team_rating: float
    sentiment_distribution: Dict[str, int]
    recent_feedback: List[Dict]

class TeamMemberStats(BaseModel):
    id: int
    name: str
    email: str
    feedback_count: int
    avg_rating: float
    last_feedback_date: Optional[datetime]
    sentiment: Optional[str]
# ----------- Routes -----------

#------------------------Autentication------------------
@app.post("/register")
def register(data: RegisterInput):
    create_user(data.name, data.email, data.password, data.role)
    return {"message": "User registered successfully"}

@app.post("/login")
def login(data: LoginInput):
    token = login_user(data.email, data.password)
    return {"token": token}

#------------------------Feedback Form------------------   
@app.post("/feedback")
def feedback(
    data: FeedbackCreate,
    manager_email: str = Depends(get_current_user)
):
    return submit_feedback(data, manager_email)

@app.put("/feedback/{feedback_id}")
def update_feedback_route(
    feedback_id: int,
    data: FeedbackCreate,
    manager_email: str = Depends(get_current_user)
):
    return update_feedback_db(feedback_id, data, manager_email)

@app.delete("/feedback/{feedback_id}")
def delete_feedback_route(
    feedback_id: int,
    manager_email: str = Depends(get_current_user)
):
    return delete_feedback(feedback_id, manager_email)

#------------------Teams--------------------

@app.get("/employees/unassigned")
def get_unassigned_employees_endpoint(manager_email: str = Depends(get_current_user)):
    """Endpoint to get all employees not assigned to any manager"""
    return get_unassigned_employees(manager_email)

@app.get("/manager/teams")
def get_manager_teams_route(
    manager_email: str = Depends(get_current_user)
):
    return get_manager_teams(manager_email)

@app.post("/manager/team/add")
def create_team_route(
    data: TeamCreate,  # Use the TeamCreate Pydantic model
    manager_email: str = Depends(get_current_user)
):
    """Endpoint to add an employee to manager's team"""
    return add_team_member(data.employee_email, manager_email)

@app.delete("/manager/team/{employee_id}")
def remove_team_member_route(
    employee_id: int,
    manager_email: str = Depends(get_current_user)
):
    return remove_team_member(manager_email, employee_id)

#----------------Feedback Acknowledgement----------------------
@app.post("/feedback/{feedback_id}/acknowledge")
def acknowledge_feedback_route(
    feedback_id: int,
    comment: str = Body(None, embed=True),
    current_user: str = Depends(get_current_user)
):
    """Endpoint for employees to acknowledge feedback"""
    return acknowledge_feedback(feedback_id,current_user,comment)

@app.get("/feedback/{feedback_id}/acknowledgment") 
def get_feedback_acknowledgment_route(
    feedback_id: int,
    current_user: str = Depends(get_current_user)
):
    """Endpoint to get acknowledgment details for specific feedback"""
    return get_feedback_acknowledgment(feedback_id, current_user)

#-----------------Feedback History ------------------------

#history_of_employee_of _their_team 
@app.get("/feedback/history/{employee_id}")
def get_feedback_history_endpoint(
    employee_id: int,
    current_user: str = Depends(get_current_user)
):
    """Get feedback history for an employee"""
    return get_feedback_history(employee_id, current_user)

#information_of_employee
@app.get("/employees/{employee_id}")
def get_employee_endpoint(
    employee_id: int,
    current_user: str = Depends(get_current_user)
):
    """Get employee details by ID"""
    return get_employee_details(employee_id, current_user)

#history_of_their feedback received
@app.get("/feedback/employee/{employee_id}")
def get_employee_feedback_route(
    employee_id: int,
    current_user: str = Depends(get_current_user)
):
    """Get feedback for a specific employee"""
    return get_employee_feedback(employee_id, current_user)

#----------Employee Dashboards-------------------
@app.get("/employee/dashboard/stats", response_model=EmployeeDashboardStats)
def get_employee_dashboard_stats_endpoint(
    current_user: str = Depends(get_current_user)
):
    """Get dashboard statistics for employee"""
    return get_employee_dashboard_stats(current_user)

@app.get("/employee/feedback/timeline", response_model=List[FeedbackTimelineResponse])
def get_employee_feedback_timeline_endpoint(
    time_filter: str = Query("all", regex="^(all|month|quarter|year)$"),
    current_user: str = Depends(get_current_user)
):
    """Get feedback timeline for employee with time filtering"""
    return get_employee_feedback_timeline(time_filter, current_user)


#------Manager Dashboard-----------
@app.get("/manager/dashboard/overview", response_model=TeamOverviewStats)
def get_manager_dashboard_overview_endpoint(
    current_user: str = Depends(get_current_user)
):
    """Get overview statistics for manager's team"""
    return get_manager_dashboard_overview(current_user)

@app.get("/manager/dashboard/team-stats", response_model=List[TeamMemberStats])
def get_team_member_stats_endpoint(
    current_user: str = Depends(get_current_user)
):
    """Get detailed statistics for each team member"""
    return get_team_member_stats(current_user)

@app.get("/manager/dashboard/feedback-trends")
def get_feedback_trends_endpoint(
    time_range: str = Query("month", regex="^(week|month|quarter|year)$"),
    current_user: str = Depends(get_current_user)
):
    """Get feedback trends over time"""
    return get_feedback_trends(time_range, current_user)



