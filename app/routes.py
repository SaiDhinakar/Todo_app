from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app import app, db, bcrypt
from app.models import User, Todo, Project
from datetime import datetime
from dateutil.relativedelta import relativedelta

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    
    return render_template('login.html')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/dashboard")
@login_required
def dashboard():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    todos = Todo.query.filter_by(user_id=current_user.id, completed=False).all()
    completed_todos = Todo.query.filter_by(user_id=current_user.id, completed=True).all()
    
    return render_template('dashboard.html', projects=projects, todos=todos, completed_todos=completed_todos)

@app.route("/create_project", methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        project = Project(name=name, description=description, user_id=current_user.id)
        db.session.add(project)
        db.session.commit()
        
        flash('Your project has been created!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('create_project.html')

@app.route("/create_todo", methods=['GET', 'POST'])
@login_required
def create_todo():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        project_id = request.form.get('project')
        
        todo = Todo(
            title=title, 
            description=description, 
            due_date=datetime.strptime(due_date, '%Y-%m-%d') if due_date else None,
            user_id=current_user.id,
            project_id=project_id if project_id else None
        )
        db.session.add(todo)
        db.session.commit()
        
        flash('Your todo has been created!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('create_todo.html', projects=projects)

@app.route("/complete_todo/<int:todo_id>", methods=['POST'])
@login_required
def complete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    
    if todo.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    todo.completed = True
    db.session.commit()
    
    # Check if the project is complete
    if todo.project:
        project = todo.project
        project_todos = Todo.query.filter_by(project_id=project.id).all()
        if all(t.completed for t in project_todos):
            project.completed = True
            project.end_date = datetime.utcnow()
            db.session.commit()
    
    flash('Todo marked as complete!', 'success')
    return redirect(url_for('dashboard'))

@app.route("/project_analytics/<int:project_id>")
@login_required
def project_analytics(project_id):
    project = Project.query.get_or_404(project_id)
    
    if project.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    todos = Todo.query.filter_by(project_id=project_id).all()
    total_todos = len(todos)
    completed_todos = len([t for t in todos if t.completed])
    completion_percentage = (completed_todos / total_todos * 100) if total_todos > 0 else 0
    
    project_duration = relativedelta(project.end_date or datetime.utcnow(), project.start_date)
    
    return render_template('project_analytics.html', 
        project=project, 
        todos=todos, 
        total_todos=total_todos, 
        completed_todos=completed_todos,
        completion_percentage=completion_percentage,
        project_duration=project_duration
    )