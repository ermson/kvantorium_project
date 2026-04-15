from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from .models import Student, Project, ProjectStage, Mentor
from datetime import date
import openpyxl
from openpyxl.styles import Font, Alignment


# ==================== АВТОРИЗАЦИЯ ====================

def login_view(request):
    """Страница входа в систему"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'core/login.html', {'error': 'Неверный логин или пароль'})
    return render(request, 'core/login.html')


def logout_view(request):
    """Выход из системы"""
    logout(request)
    return redirect('login')


# ==================== ДАШБОРД ====================

# @login_required
# @login_required
def dashboard(request):
    students_count = Student.objects.count()
    projects_count = Project.objects.count()
    in_progress_count = Project.objects.filter(status='development').count()
    urgent_stages = ProjectStage.objects.filter(is_completed=False).count()
    urgent_projects = Project.objects.filter(status__in=['idea', 'development'])[:5]

    context = {
        'students_count': students_count,
        'projects_count': projects_count,
        'in_progress_count': in_progress_count,
        'urgent_stages': urgent_stages,
        'urgent_projects': urgent_projects,
    }
    return render(request, 'core/dashboard.html', context)
# ==================== УВЕДОМЛЕНИЯ ====================

def get_notifications(request):
    """Получение уведомлений для текущего пользователя (просроченные этапы)"""
    if not request.user.is_authenticated:
        return []

    today = date.today()
    stages = ProjectStage.objects.filter(
        is_completed=False,
        planned_date__lte=today
    ).select_related('project', 'project__student')[:10]

    notifications = []
    for stage in stages:
        days_overdue = (today - stage.planned_date).days
        notifications.append({
            'id': stage.id,
            'message': f"Этап «{stage.stage_name}» проекта «{stage.project.name}» просрочен на {days_overdue} дн.",
            'url': f"/stages/{stage.id}/",
        })

    return notifications


def notifications_context(request):
    """Контекстный процессор для уведомлений (доступен на всех страницах)"""
    return {'notifications': get_notifications(request)}


# ==================== УЧЕНИКИ (STUDENTS) ====================

@login_required
def student_list(request):
    """Список всех учеников с поиском и фильтрацией"""
    students = Student.objects.all()

    # Поиск по ФИО
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(last_name__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(middle_name__icontains=search_query)
        )

    # Фильтр по направлению (группе)
    group_filter = request.GET.get('group', '')
    if group_filter:
        students = students.filter(group_name=group_filter)

    # Получаем уникальные направления для выпадающего списка фильтра
    groups = Student.objects.values_list('group_name', flat=True).distinct()

    context = {
        'students': students,
        'search_query': search_query,
        'group_filter': group_filter,
        'groups': groups,
    }
    return render(request, 'core/student_list.html', context)


@login_required
def student_detail(request, pk):
    """Детальная страница ученика с его проектами"""
    student = get_object_or_404(Student, pk=pk)
    projects = student.project_set.all()
    return render(request, 'core/student_detail.html', {'student': student, 'projects': projects})


@login_required
def student_create(request):
    """Создание нового ученика"""
    if request.method == 'POST':
        student = Student.objects.create(
            last_name=request.POST['last_name'],
            first_name=request.POST['first_name'],
            middle_name=request.POST.get('middle_name', ''),
            group_name=request.POST['group_name'],
            mentor_id=request.POST['mentor'],
            enrollment_date=request.POST['enrollment_date']
        )
        return redirect('student_list')

    mentors = Mentor.objects.all()
    group_choices = [
        'Промышленная робототехника',
        'VR/AR (Виртуальная реальность)',
        'Хайтек (High-tech)',
        'IT (Информационные технологии)',
        'Био (Биотехнологии)',
        'Промдизайн (Промышленный дизайн)',
    ]
    return render(request, 'core/student_form.html', {
        'mentors': mentors,
        'group_choices': group_choices,
    })


@login_required
def student_edit(request, pk):
    """Редактирование ученика"""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.last_name = request.POST['last_name']
        student.first_name = request.POST['first_name']
        student.middle_name = request.POST.get('middle_name', '')
        student.group_name = request.POST['group_name']
        student.mentor_id = request.POST['mentor']
        student.enrollment_date = request.POST['enrollment_date']
        student.save()
        return redirect('student_list')

    mentors = Mentor.objects.all()
    group_choices = [
        'Промышленная робототехника',
        'VR/AR (Виртуальная реальность)',
        'Хайтек (High-tech)',
        'IT (Информационные технологии)',
        'Био (Биотехнологии)',
        'Промдизайн (Промышленный дизайн)',
    ]
    return render(request, 'core/student_form.html', {
        'student': student,
        'mentors': mentors,
        'group_choices': group_choices,
    })


@login_required
def student_delete(request, pk):
    """Удаление ученика"""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.delete()
        return redirect('student_list')
    return render(request, 'core/confirm_delete.html', {'object': student, 'type': 'student'})


# ==================== ПРОЕКТЫ (PROJECTS) ====================

@login_required
def project_list(request):
    """Список проектов с поиском и фильтрацией"""
    projects = Project.objects.all()

    # Поиск по названию
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(name__icontains=search_query)

    # Фильтр по статусу
    status_filter = request.GET.get('status', '')
    if status_filter:
        projects = projects.filter(status=status_filter)

    # Статусы для выпадающего списка
    status_choices = Project.STATUS_CHOICES

    context = {
        'projects': projects,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': status_choices,
    }
    return render(request, 'core/project_list.html', context)


@login_required
def project_detail(request, pk):
    """Детальная страница проекта"""
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'core/project_detail.html', {'project': project})


@login_required
def project_create(request):
    """Создание нового проекта"""
    if request.method == 'POST':
        project = Project.objects.create(
            name=request.POST['name'],
            description=request.POST['description'],
            student_id=request.POST['student'],
            status=request.POST['status']
        )
        return redirect('project_list')
    students = Student.objects.all()
    return render(request, 'core/project_form.html', {'students': students})


@login_required
def project_edit(request, pk):
    """Редактирование проекта"""
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.name = request.POST['name']
        project.description = request.POST['description']
        project.student_id = request.POST['student']
        project.status = request.POST['status']
        project.save()
        return redirect('project_list')
    students = Student.objects.all()
    return render(request, 'core/project_form.html', {'project': project, 'students': students})


@login_required
def project_delete(request, pk):
    """Удаление проекта"""
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.delete()
        return redirect('project_list')
    return render(request, 'core/confirm_delete.html', {'object': project, 'type': 'project'})


# ==================== ЭКСПОРТ В EXCEL ====================

@login_required
def export_projects_excel(request):
    """Экспорт списка проектов в Excel"""
    # Создаём новую книгу Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Проекты"

    # Заголовки
    headers = ['ID', 'Название проекта', 'Ученик', 'Статус', 'Дата создания']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # Данные
    projects = Project.objects.all().select_related('student')
    for row, project in enumerate(projects, 2):
        ws.cell(row=row, column=1, value=project.id)
        ws.cell(row=row, column=2, value=project.name)
        ws.cell(row=row, column=3, value=f"{project.student.last_name} {project.student.first_name}")
        ws.cell(row=row, column=4, value=project.get_status_display())
        ws.cell(row=row, column=5, value=project.created_at.strftime('%d.%m.%Y'))

    # Автоматическая ширина колонок
    for col in range(1, 6):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 25

    # Формируем ответ
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="projects_export.xlsx"'
    wb.save(response)
    return response


# ==================== ЭТАПЫ (STAGES) ====================

@login_required
def stage_list(request):
    """Список этапов с поиском и фильтрацией"""
    stages = ProjectStage.objects.all().order_by('planned_date')

    # Поиск по названию этапа
    search_query = request.GET.get('search', '')
    if search_query:
        stages = stages.filter(stage_name__icontains=search_query)

    # Фильтр по выполнению
    completed_filter = request.GET.get('completed', '')
    if completed_filter == 'completed':
        stages = stages.filter(is_completed=True)
    elif completed_filter == 'not_completed':
        stages = stages.filter(is_completed=False)

    context = {
        'stages': stages,
        'search_query': search_query,
        'completed_filter': completed_filter,
    }
    return render(request, 'core/stage_list.html', context)


@login_required
def stage_detail(request, pk):
    """Детальная страница этапа"""
    stage = get_object_or_404(ProjectStage, pk=pk)
    return render(request, 'core/stage_detail.html', {'stage': stage})


@login_required
def stage_create(request):
    """Создание нового этапа"""
    if request.method == 'POST':
        stage = ProjectStage.objects.create(
            project_id=request.POST['project'],
            stage_name=request.POST['stage_name'],
            planned_date=request.POST['planned_date'],
            actual_date=request.POST.get('actual_date') or None,
            is_completed=request.POST.get('is_completed') == 'on',
            comment=request.POST.get('comment', '')
        )
        return redirect('stage_list')
    projects = Project.objects.all()
    return render(request, 'core/stage_form.html', {'projects': projects})


@login_required
def stage_edit(request, pk):
    """Редактирование этапа"""
    stage = get_object_or_404(ProjectStage, pk=pk)
    if request.method == 'POST':
        stage.project_id = request.POST['project']
        stage.stage_name = request.POST['stage_name']
        stage.planned_date = request.POST['planned_date']
        stage.actual_date = request.POST.get('actual_date') or None
        stage.is_completed = request.POST.get('is_completed') == 'on'
        stage.comment = request.POST.get('comment', '')
        stage.save()
        return redirect('stage_list')
    projects = Project.objects.all()
    return render(request, 'core/stage_form.html', {'stage': stage, 'projects': projects})


@login_required
def stage_delete(request, pk):
    """Удаление этапа"""
    stage = get_object_or_404(ProjectStage, pk=pk)
    if request.method == 'POST':
        stage.delete()
        return redirect('stage_list')
    return render(request, 'core/confirm_delete.html', {'object': stage, 'type': 'stage'})