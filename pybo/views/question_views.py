import os
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, g, flash, current_app
from werkzeug.utils import secure_filename

from pybo import db
from pybo.forms import QuestionForm, AnswerForm
from pybo.models import Question, Answer, User
from pybo.views.auth_views import login_required

bp = Blueprint('question', __name__, url_prefix='/question')

@bp.route('/list/')
def _list():
    page = request.args.get('page', default=1, type=int)  # 페이지
    kw = request.args.get('kw', default='', type=str)   # 검색 키워드
    question_list = Question.query.order_by(Question.create_date.desc())
    if kw:
        search = f'%%{kw}%%'
        sub_query = db.session.query(Answer.question_id, Answer.content, User.username) \
            .join(User, Answer.user_id == User.id).subquery()
        question_list = question_list.join(User) \
            .outerjoin(sub_query, sub_query.c.question_id == Question.id) \
            .filter(Question.subject.ilike(search) |  # 질문제목
                    Question.content.ilike(search) |  # 질문내용
                    User.username.ilike(search) |  # 질문작성자
                    sub_query.c.content.ilike(search) |  # 답변내용
                    sub_query.c.username.ilike(search)  # 답변작성자
                    ) \
            .distinct()
    question_list = question_list.paginate(page=page, per_page=10)  # 한 페이지에 보여야할 게시글 수
    return render_template('question/question_list.html',
                           question_list=question_list, page=page, kw=kw)

@bp.route('/detail/<int:question_id>')
def detail(question_id):
    form = AnswerForm()  # 질문 상세 템플릿에 답변 폼 추가
    question = Question.query.get_or_404(question_id)
    return render_template('question/question_detail.html', question=question, form=form)

@bp.route('/create/', methods=['GET', 'POST'])
@login_required
def create():
    form = QuestionForm()
    if request.method == 'POST' and form.validate_on_submit():
        # 폼에서 받은 이미지 파일 처리
        image_file = form.image.data
        image_path = None

        if image_file:
            # 저장 경로 설정 : 오늘 날짜 폴더 생성
            today = datetime.now().strftime('%Y%m%d')
            upload_folder = os.path.join(current_app.root_path, 'static/photo', today)
            os.makedirs(upload_folder, exist_ok=True)

            # 파일 저장
            filename = secure_filename(image_file.filename)
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)

            # DB에는 파일 저장 경로만 넣어줌(static 기준으로 상대경로)
            image_path = f'photo/{today}/{filename}'

        question = Question(subject=form.subject.data,
                            content=form.content.data,
                            create_date=datetime.now(),
                            user_id=g.user.id,
                            image_path=image_path
                            )
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('question/question_form.html', form=form)

@bp.route('/modify/<int:question_id>', methods=['GET', 'POST'])
@login_required
def modify(question_id):
    question = Question.query.get_or_404(question_id)
    if g.user != question.user:
        flash('수정권한이 없습니다.')
        return redirect(url_for('question.detail', question_id=question_id))
    if request.method == 'POST':  # POST요청
        form = QuestionForm()
        if form.validate_on_submit():
            form.populate_obj(question)
            question.modify_date = datetime.now()
            db.session.commit()
            return redirect(url_for('question.detail', question_id=question_id))
    else:  # GET요청
        form = QuestionForm(obj=question)
    return render_template('/question/question_form.html', form=form)

@bp.route('/delete/<int:question_id>')
@login_required
def delete(question_id):
    question = Question.query.get_or_404(question_id)
    if g.user != question.user:
        flash('삭제권한이 없습니다.')
        return redirect(url_for('question.detail', question_id=question_id))
    else:
        db.session.delete(question)
        db.session.commit()
    return redirect(url_for('question._list'))