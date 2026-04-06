from django.db import models
from django.contrib.auth.models import User  # Встроенная модель пользователя


# Модель "Наставник" (расширяет встроенного пользователя)
class Mentor(models.Model):
    # Связь один-к-одному со встроенным пользователем Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    # Дополнительные поля
    department = models.CharField(max_length=100, verbose_name="Квантум/направление")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"

    class Meta:
        verbose_name = "Наставник"
        verbose_name_plural = "Наставники"


# Модель "Обучающийся"
class Student(models.Model):
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    middle_name = models.CharField(max_length=50, blank=True, verbose_name="Отчество")
    group_name = models.CharField(max_length=50, verbose_name="Группа/Квантум")
    # Связь с наставником (один наставник может вести много учеников)
    mentor = models.ForeignKey(Mentor, on_delete=models.SET_NULL, null=True, verbose_name="Наставник")
    enrollment_date = models.DateField(verbose_name="Дата поступления")

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name = "Обучающийся"
        verbose_name_plural = "Обучающиеся"


# Модель "Проект"
class Project(models.Model):
    # Статусы проекта (ограниченный набор значений)
    STATUS_CHOICES = [
        ('idea', 'Идея'),
        ('development', 'В разработке'),
        ('review', 'На проверке'),
        ('completed', 'Завершен'),
        ('defended', 'Защищен'),
    ]

    name = models.CharField(max_length=200, verbose_name="Название проекта")
    description = models.TextField(verbose_name="Описание")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Обучающийся")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idea', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"


# Модель "Этап проекта"
class ProjectStage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="Проект")
    stage_name = models.CharField(max_length=100, verbose_name="Название этапа")
    planned_date = models.DateField(verbose_name="Плановая дата")
    actual_date = models.DateField(null=True, blank=True, verbose_name="Фактическая дата")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнен")
    comment = models.TextField(blank=True, verbose_name="Комментарий наставника")

    def __str__(self):
        return f"{self.project.name} - {self.stage_name}"

    class Meta:
        verbose_name = "Этап проекта"
        verbose_name_plural = "Этапы проектов"
        ordering = ['planned_date']  # Сортировка по дате


from django.db import models

# Create your models here.
