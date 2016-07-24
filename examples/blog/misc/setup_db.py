def setup():
    from blog.models import Blog, Article, Comment, Category
    blogs = []
    for title in ["blog1", "blog2"]:
        blogs.append(Blog(title=title))
    Blog.objects.bulk_create(blogs)
    blogs = list(Blog.objects.all().order_by("id"))

    for blog in blogs:
        articles = []
        for title in ["hello world", "good bye world"]:
            articles.append(Article(title=title, content=title, blog=blog))
        Article.objects.bulk_create(articles)
        articles = list(Article.objects.all().order_by("id"))

        for article in articles:
            comments = []
            for comment in ["comment1", "comment2", "comment3"]:
                comments.append(Comment(title="anonymous", content=comment, article=article))
            Comment.objects.bulk_create(comments)
            comments = list(Comment.objects.all().order_by("id"))

    categories = []
    for name in ["hello", "good-bye"]:
        categories.append(Category(name=name))
    Category.objects.bulk_create(categories)
    categories = list(Category.objects.all().order_by("id"))

    for article in Article.objects.filter(title__startswith="hello"):
        categories[0].articles.add(article)
    for article in Article.objects.filter(title__startswith="good-bye"):
        categories[1].articles.add(article)
    for category in categories:
        category.save()
